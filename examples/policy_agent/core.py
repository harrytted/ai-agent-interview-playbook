"""A bounded runtime with visible observations and durable task state.

Only this controller loads task IDs/fixtures. Neither policy receives them.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import re
import time

from . import policies
from .storage import Stores, fingerprint

DATA = Path(__file__).parent / "data"
USER_FILE = DATA / "users.json"
DEFAULT_ROOT = Path(".local/policy_agent")
READ_TOOLS = {"search_policy", "get_policy", "lookup_ticket"}
OUTPUT_STATUSES = {"answered", "clarification_required", "human_required", "insufficient_evidence"}


def _schema(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


TEXT = {"type": "string", "minLength": 1, "maxLength": 256}
TOOLS = {
    "search_policy": _schema({"query": {**TEXT, "enum": ["lodging", "consultation", "meal", "office", "finance", "untrusted"], "description": "本教材固定主题键，不是自然语言或向量搜索。lodging=住宿，consultation=咨询材料，meal=餐补。"}, "city": TEXT, "trip_date": {"type": "string", "format": "date"}}),
    "get_policy": _schema({"policy_id": TEXT, "trip_date": {"type": "string", "format": "date"}}),
    "create_ticket": _schema({"title": TEXT, "city": TEXT, "trip_date": {"type": "string", "format": "date"}, "amount_cny": {"type": "integer", "minimum": 0, "maximum": 1000000}, "evidence_refs": {"type": "array", "items": TEXT, "minItems": 1}}),
    "lookup_ticket": _schema({"operation_id": TEXT}),
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_task(task_id, variant="default"):
    tasks = read_json(DATA / "tasks.json")
    task = next((deepcopy(t) for t in tasks if t["task_id"] == task_id), None)
    if task is None:
        raise ValueError("unknown task")
    variants = read_json(DATA / "variants.json")
    if variant != "default":
        if variant not in variants:
            raise ValueError("unknown variant")
        change = variants[variant]
        for name in ("goal", "user_id"):
            if name in change:
                task[name] = change[name]
        if "known" in change:
            task["known"] = deepcopy(change["known"])
        for name in change.get("remove_known", []):
            task["known"].pop(name, None)
        task["fixture"] = change.get("fault", task.get("fixture"))
        task["update_after_approval"] = change.get("user_update_after_approval")
    task["variant"] = variant
    return task


def run_directory(root, run_id):
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ValueError("run-id permits 1–80 letters, digits, underscore and hyphen")
    return Path(root) / run_id


def subject(state):
    user = read_json(USER_FILE).get(state["user_id"])
    if not user:
        raise ValueError("unknown trusted demo identity")
    return {"user_id": state["user_id"], **user}


def is_authorized(document, user):
    return document["tenant_id"] == user["tenant_id"] and user["role"] in document["allowed_roles"]


def can_access_run(state):
    user = subject(state)
    return user["tenant_id"] == state["initial_tenant"] and user["role"] in {"staff", "manager"}


def applicable(document, state, user, *, trip_date=None):
    dates = [trip_date] if trip_date else state["known"].get("trip_dates", [state["known"].get("trip_date")])
    return is_authorized(document, user) and (document["topic"] != "lodging" or document["employee_category"] == user["employee_category"]) and any(d and document["valid_from"] <= d and (document["valid_to"] is None or d < document["valid_to"]) for d in dates)


def build_context(state):
    user = subject(state)  # Always reload current permissions, including resume.
    if not can_access_run(state):
        return {"goal": "当前身份不可访问此已保存任务。", "messages": [], "known": {}, "unknowns": [], "observations": [], "evidence": []}
    known = deepcopy(state["known"])
    known["employee_category"] = user["employee_category"]
    cities = known.get("cities", [known.get("city")])
    observations, evidence = [], {}
    for raw in state["observations"]:
        observation = deepcopy(raw)
        if observation["name"] in {"search_policy", "get_policy"}:
            documents = [d for d in observation["result"]["data"].get("documents", []) if is_authorized(d, user)]
            observation["result"]["data"]["documents"] = documents
            allowed_refs = {c["clause_id"] for d in documents for c in d["clauses"]}
            observation["result"]["evidence_refs"] = [r for r in observation["result"]["evidence_refs"] if r in allowed_refs]
            # Re-evaluate old observations against current applicability/ACL.
            # A city change invalidates old-city evidence; an amount change
            # does not invalidate the same effective policy document.
            if observation["result"]["status"] == "ok":
                for d in documents:
                    if applicable(d, state, user) and (not d["city"] or d["city"] in cities):
                        evidence[d["document_id"]] = d
        observations.append(observation)
    return {"goal": state["goal"], "messages": deepcopy(state["messages"]), "known": known, "unknowns": list(state["unknowns"]), "observations": observations, "evidence": list(evidence.values())}


def validate_call(action, state):
    if not isinstance(action, dict) or set(action) != {"call_id", "name", "arguments"}:
        raise ValueError("action requires exactly call_id/name/arguments")
    if not isinstance(action["call_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", action["call_id"]):
        raise ValueError("invalid call_id")
    name, args = action["name"], action["arguments"]
    if not isinstance(name, str) or name not in TOOLS or not isinstance(args, dict) or set(args) != set(TOOLS[name]["required"]):
        raise ValueError("unknown tool or unexpected/missing arguments")
    if state["mode"] == "live" and name not in {"search_policy", "get_policy"}:
        raise ValueError("live only permits read-only policy tools")
    for key, schema in TOOLS[name]["properties"].items():
        value = args[key]
        if schema["type"] == "string":
            if not isinstance(value, str) or not value.strip() or len(value) > schema.get("maxLength", 256):
                raise ValueError("invalid string field: " + key)
            if schema.get("format") == "date":
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError("invalid date")
            if "enum" in schema and value not in schema["enum"]:
                raise ValueError("query must be a documented topic key")
        elif schema["type"] == "integer":
            if type(value) is not int or not schema["minimum"] <= value <= schema["maximum"]:
                raise ValueError("invalid integer field: " + key)
        elif schema["type"] == "array":
            if not isinstance(value, list) or not value or len(value) > 16 or any(not isinstance(x, str) or not x or len(x) > 256 for x in value) or len(set(value)) != len(value):
                raise ValueError("invalid evidence_refs")
    user = subject(state)
    if name == "lookup_ticket":
        operations = {c.get("operation_id") for c in state["pending_calls"]}
        if args["operation_id"] not in operations:
            raise PermissionError("permission_denied: unknown operation for this task")
    if name == "get_policy":
        docs = [d for d in read_json(DATA / "policies.json") if d["policy_id"] == args["policy_id"]]
        if docs and not any(is_authorized(d, user) for d in docs):
            raise PermissionError("permission_denied: requested resource is unavailable to current identity")
    if name == "search_policy" and user["tenant_id"] != "demo-a":
        raise PermissionError("permission_denied: no accessible corpus for current tenant")
    if name == "create_ticket":
        known = state["known"]
        if not known.get("create_ticket") or any(args[k] != known.get(k) for k in ("title", "city", "trip_date", "amount_cny")):
            raise PermissionError("write does not match explicit current user request")
        refs = {c["clause_id"] for d in build_context(state)["evidence"] for c in d["clauses"]}
        if not set(args["evidence_refs"]) <= refs:
            raise PermissionError("write lacks currently obtained authorized evidence")
    return deepcopy(action)


def _tool_result(action, status="ok", *, documents=None, data=None, error=None):
    if data is None:
        data = {"documents": documents or [], "rejected": []}
    refs = [c["clause_id"] for d in (documents or []) for c in d["clauses"]]
    return {"call_id": action["call_id"], "status": status, "data": data, "evidence_refs": refs, "error": error}


def _read(action, state):
    name, args = action["name"], action["arguments"]
    documents = read_json(DATA / "policies.json")
    user = subject(state)
    if name == "get_policy":
        documents = [d for d in documents if d["policy_id"] == args["policy_id"]]
    else:
        documents = [d for d in documents if d["topic"] == args["query"] and d["city"] in ("", args["city"])]
    documents = [d for d in documents if is_authorized(d, user) and (d["topic"] != "lodging" or d["employee_category"] == user["employee_category"])]
    fault = state.get("fixture")
    if fault == "read-transient" and not state["faults_used"].get("read-transient"):
        state["faults_used"]["read-transient"] = True
        return _tool_result(action, "error", error={"code": "temporary_read_failure", "message": "injected transient read failure", "retryable": True})
    if fault == "empty-result":
        documents = []
    elif fault == "no-current-source":
        documents = [d for d in documents if d["document_id"] != "P17-v2"]
    elif fault == "stale-first" and name == "search_policy" and not state["faults_used"].get("stale-first"):
        state["faults_used"]["stale-first"] = True
        old = [d for d in documents if not applicable(d, state, user, trip_date=args["trip_date"])]
        return _tool_result(action, "stale_evidence", documents=old)
    current = [d for d in documents if applicable(d, state, user, trip_date=args["trip_date"])]
    if fault == "conflicting-current" and current:
        conflict = deepcopy(current[0])
        conflict["document_id"] = "P17-conflict-v2"
        conflict["clauses"] = [{"clause_id": "P17-conflict-v2#4", "text": "同等级来源的冲突夹具：每晚500元。", "amount_cny": 500}]
        return _tool_result(action, "conflicting_evidence", documents=current + [conflict])
    if fault == "untrusted-instruction" and current and name == "search_policy":
        current += [d for d in read_json(DATA / "policies.json") if d["policy_id"] in {"P22", "P23"} and is_authorized(d, user)]
    if current:
        return _tool_result(action, documents=current)
    if documents:
        return _tool_result(action, "stale_evidence", documents=documents)
    return _tool_result(action, "empty")


def _emit(stores, state, event, **payload):
    state["seq"] += 1
    record = {"task_id": state["task_id"], "run_id": state["run_id"], "seq": state["seq"], "state_revision": state["revision"], "event": event, **payload}
    # Persist state before the event can authorize execution; flush before crash.
    stores.save(state)
    with (stores.run_dir / "trace.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _stop(stores, state, status, *, output=None, detail=None):
    state["status"] = status
    if output is not None:
        state["output"] = output
    _emit(stores, state, "waiting" if status in {"clarification_required", "approval_required", "write_outcome_unknown"} else "stopped", status=status, detail=detail)
    context = build_context(state)
    state["evidence_refs"] = sorted({c["clause_id"] for d in context["evidence"] for c in d["clauses"]})
    stores.save(state)
    private = status != "permission_denied"
    result = {"task_id": state["task_id"], "run_id": state["run_id"], "variant": state["variant"], "mode": state["mode"], "status": status, "output": state.get("output") if private else None, "budget": state["budget"], "evidence_refs": state["evidence_refs"], "created_count": len(stores.snapshot()) if private else 0, "approval_request": state.get("approval_request") if private else None, "operation_id": state.get("operation_id") if private else None, "object_id": state.get("object_id") if private else None, "detail": detail}
    write_json(stores.run_dir / "context.json", context)
    write_json(stores.run_dir / "result.json", result)
    return result


def _validate_decision(decision):
    if not isinstance(decision, dict) or set(decision) != {"tool_calls", "output"} or not isinstance(decision["tool_calls"], list):
        raise ValueError("decision requires tool_calls/output")
    calls, output = decision["tool_calls"], decision["output"]
    if calls:
        if any(not isinstance(call, dict) for call in calls):
            raise ValueError("tool_calls must contain objects")
        if output is not None:
            raise ValueError("tool requests and final output are mutually exclusive")
        return
    if not isinstance(output, dict) or set(output) != {"status", "claims", "evidence_refs", "answer", "requested_fields"} or not isinstance(output["status"], str) or output["status"] not in OUTPUT_STATUSES:
        raise ValueError("invalid structured output")
    if not isinstance(output["answer"], str) or not isinstance(output["claims"], list) or not isinstance(output["evidence_refs"], list) or not isinstance(output["requested_fields"], list):
        raise ValueError("invalid output field types")
    fields = output["requested_fields"]
    if any(not isinstance(field, str) or not field for field in fields) or len(set(fields)) != len(fields):
        raise ValueError("requested_fields must contain unique field names")
    if output["status"] != "clarification_required" and output["requested_fields"]:
        raise ValueError("only clarification can request fields")


def _validate_claims(output, state):
    evidence = build_context(state)["evidence"]
    clauses = {c["clause_id"]: (d, c) for d in evidence for c in d["clauses"]}
    if not all(isinstance(r, str) and r in clauses for r in output["evidence_refs"]):
        raise ValueError("answer cites unobserved or inapplicable evidence")
    if output["status"] == "answered" and not output["claims"]:
        raise ValueError("answered requires checkable claims")
    for claim in output["claims"]:
        if not isinstance(claim, dict) or not isinstance(claim.get("clause_id"), str) or claim["clause_id"] not in clauses:
            raise ValueError("claim lacks current evidence")
        document, clause = clauses[claim["clause_id"]]
        if claim.get("document_id") != document["document_id"] or claim["clause_id"] not in output["evidence_refs"]:
            raise ValueError("claim evidence mismatch")
        if claim.get("kind") == "lodging_limit":
            required = {"kind", "city", "trip_date", "amount_cny", "document_id", "clause_id"}
            requested_dates = state["known"].get("trip_dates", [state["known"].get("trip_date")])
            if set(claim) != required or claim["city"] != document["city"] or claim["trip_date"] not in requested_dates or type(claim["amount_cny"]) is not int or claim["amount_cny"] != clause.get("amount_cny") or not applicable(document, state, subject(state), trip_date=claim["trip_date"]):
                raise ValueError("unsupported amount claim")
        elif claim.get("kind") == "required_materials":
            if set(claim) != {"kind", "items", "document_id", "clause_id"} or claim["items"] != clause.get("items"):
                raise ValueError("unsupported material claim")
        else:
            raise ValueError("unknown claim kind")


def _validate_output_evidence(output, state):
    if output["status"] == "answered":
        _validate_claims(output, state)
        return
    if output["claims"]:
        _validate_claims(output, state)
    user = subject(state)
    observed = {c["clause_id"] for o in state["observations"] if o["name"] in {"search_policy", "get_policy"} and o["result"]["status"] in {"ok", "conflicting_evidence"} for d in o["result"]["data"].get("documents", []) if applicable(d, state, user) for c in d["clauses"]}
    if any(not isinstance(ref, str) or ref not in observed for ref in output["evidence_refs"]):
        raise ValueError("non-answer cites unobserved or unauthorized evidence")
    if output["status"] == "human_required":
        conflicts = [o for o in state["observations"] if o["result"]["status"] == "conflicting_evidence"]
        values = {c["amount_cny"] for o in conflicts for d in o["result"]["data"].get("documents", []) if applicable(d, state, user) for c in d["clauses"] if "amount_cny" in c and c["clause_id"] in output["evidence_refs"]}
        if len(values) < 2:
            raise ValueError("human_required needs actual conflicting observations")


def render_answer(output, known):
    """The displayed amount comparison is computed, never trusted model prose."""
    sentences = []
    for claim in output["claims"]:
        if claim["kind"] == "lodging_limit":
            comparison = ""
            if "amount_cny" in known:
                comparison = "；给定金额" + ("未超过" if known["amount_cny"] <= claim["amount_cny"] else "超过") + "此金额上限"
            sentences.append(f'{claim["trip_date"]}{claim["city"]}每晚上限{claim["amount_cny"]}元{comparison}。')
        elif claim["kind"] == "required_materials":
            sentences.append("咨询材料：日期、城市、金额、咨询事由；咨询不等于批准。")
    return "".join(sentences) + "本例只核对虚构制度的金额条件。"


def _request_approval(stores, state, call):
    request = {"request_id": f'APR-{state["run_id"]}-{state["approval_sequence"] + 1}', "task_id": state["task_id"], "operation_id": call["operation_id"], "state_revision": state["revision"], "payload_hash": fingerprint(call["arguments"]), "payload": deepcopy(call["arguments"])}
    previous = state.get("approval_request")
    if previous and previous["payload_hash"] == request["payload_hash"] and previous["state_revision"] == state["revision"]:
        request = previous
    else:
        state["approval_sequence"] += 1
    state["approval_request"] = request
    return _stop(stores, state, "approval_required")


def _approval_valid(state, call):
    approved = state.get("approval")
    user = subject(state)
    return bool(approved and approved.get("task_id") == state["task_id"] and approved.get("operation_id") == call["operation_id"] and approved.get("payload_hash") == fingerprint(call["arguments"]) and approved.get("state_revision") == state["revision"] and approved.get("approver_id") == user["user_id"] and user["tenant_id"] == state["initial_tenant"] and user["role"] in {"staff", "manager"})


def _drive(stores, state, policy=None, *, crash_after_remote=False):
    state["status"] = "running"
    if not can_access_run(state):
        return _stop(stores, state, "permission_denied", detail="current identity cannot access saved task")
    started = time.monotonic()
    if policy is None:
        if state["mode"] == "live":
            from .live import LivePolicy
            try:
                policy = LivePolicy(stores.run_dir)
            except RuntimeError as exc:
                return _stop(stores, state, getattr(exc, "status", "provider_failed"), detail=str(exc))
        else:
            policy = policies.always_read if state.get("fixture") == "loop" else policies.decide
    while True:
        # Pending work is completed/reconciled before another policy decision.
        while state["next_call_index"] < len(state["pending_calls"]):
            call = state["pending_calls"][state["next_call_index"]]
            if call.get("result") is not None or call.get("cancelled"):
                state["next_call_index"] += 1
                continue
            try:
                validate_call({k: call[k] for k in ("call_id", "name", "arguments")}, state)
            except (ValueError, PermissionError) as exc:
                return _stop(stores, state, "permission_denied" if isinstance(exc, PermissionError) else "invalid_output", detail=str(exc))
            if call["name"] == "create_ticket":
                if not _approval_valid(state, call):
                    return _request_approval(stores, state, call)
                if call.get("started"):
                    # After a lost acknowledgment, query the independent service
                    # with the same operation; do not create a second intent.
                    query_id = call["call_id"] + "-reconcile"
                    attempts = state["budget"]["attempts_by_call_id"]
                    if attempts.get(query_id, 0) >= 2 or (not call.get("reconcile_started") and state["budget"]["tool_calls_started"] >= 12):
                        return _stop(stores, state, "budget_exhausted", detail="reconciliation read budget exhausted")
                    if not call.get("reconcile_started"):
                        call["reconcile_started"] = True
                        state["budget"]["tool_calls_started"] += 1
                    attempts[query_id] = attempts.get(query_id, 0) + 1
                    query = {"call_id": query_id, "name": "lookup_ticket", "arguments": {"operation_id": call["operation_id"]}}
                    _emit(stores, state, "tool_started", call_id=query_id, operation_id=call["operation_id"], name="lookup_ticket", arguments=query["arguments"], attempt=attempts[query_id])
                    ticket = stores.lookup(subject(state)["tenant_id"], call["operation_id"])
                    query_result = _tool_result(query, data={"found": ticket is not None, "operation_id": call["operation_id"], "object_id": ticket["object_id"] if ticket else None, "ticket": ticket})
                    state["observations"].append({**query, "result": query_result, "state_revision": state["revision"]})
                    _emit(stores, state, "tool_result", call_id=query_id, operation_id=call["operation_id"], name="lookup_ticket", result=query_result)
                    _emit(stores, state, "state_updated", action="reconcile", operation_id=call["operation_id"], found=ticket is not None)
                    if ticket:
                        if fingerprint({k: ticket[k] for k in call["arguments"]}) != fingerprint(call["arguments"]):
                            return _stop(stores, state, "tool_failed", detail="reconciliation content mismatch")
                        result = _tool_result(call, data={"operation_id": call["operation_id"], "object_id": ticket["object_id"], "ticket": ticket, "replayed": True})
                    else:
                        return _stop(stores, state, "write_outcome_unknown", detail="No authoritative object; explicit retry decision is required.")
                else:
                    call["started"] = True
                    state["budget"]["tool_calls_started"] += 1
                    state["operation_id"] = call["operation_id"]
                    _emit(stores, state, "tool_started", call_id=call["call_id"], operation_id=call["operation_id"], name=call["name"], arguments=call["arguments"])
                    try:
                        ticket, replayed = stores.create(subject(state)["tenant_id"], call["operation_id"], call["arguments"])
                    except ValueError as exc:
                        return _stop(stores, state, "tool_failed", detail=str(exc))
                    if state.get("fixture") == "crash-after-remote" and not state["faults_used"].get("crash-after-remote"):
                        state["faults_used"]["crash-after-remote"] = True
                        stores.save(state)
                        if crash_after_remote:
                            os._exit(73)
                        return _stop(stores, state, "write_outcome_unknown", detail="simulated lost acknowledgment; resume queries original operation")
                    result = _tool_result(call, data={"operation_id": call["operation_id"], "object_id": ticket["object_id"], "ticket": ticket, "replayed": replayed})
            elif call["name"] == "lookup_ticket":
                ticket = stores.lookup(subject(state)["tenant_id"], call["arguments"]["operation_id"])
                state["budget"]["tool_calls_started"] += 1
                _emit(stores, state, "tool_started", call_id=call["call_id"], name=call["name"], arguments=call["arguments"])
                result = _tool_result(call, data={"found": ticket is not None, "operation_id": call["arguments"]["operation_id"], "object_id": ticket["object_id"] if ticket else None, "ticket": ticket})
            else:
                attempts = state["budget"]["attempts_by_call_id"]
                if not call.get("started"):
                    call["started"] = True
                    state["budget"]["tool_calls_started"] += 1
                result = call.get("last_result")
                while attempts.get(call["call_id"], 0) < 2:
                    attempts[call["call_id"]] = attempts.get(call["call_id"], 0) + 1
                    _emit(stores, state, "tool_started", call_id=call["call_id"], name=call["name"], arguments=call["arguments"], attempt=attempts[call["call_id"]])
                    result = _read(call, state)
                    call["last_result"] = result
                    stores.save(state)
                    if not (result["error"] and result["error"]["retryable"]):
                        break
                if result is None:
                    result = _tool_result(call, "error", error={"code": "attempt_budget_exhausted", "message": "persisted read attempts exhausted", "retryable": False})
            call["result"] = result
            observation = {"call_id": call["call_id"], "name": call["name"], "arguments": deepcopy(call["arguments"]), "result": result, "state_revision": state["revision"]}
            state["observations"].append(observation)
            state["next_call_index"] += 1
            _emit(stores, state, "tool_result", call_id=call["call_id"], name=call["name"], result=result, **({"operation_id": call["operation_id"]} if call.get("operation_id") else {}))
            if call["name"] == "create_ticket":
                state["operation_id"], state["object_id"] = result["data"]["operation_id"], result["data"]["object_id"]
                return _stop(stores, state, "write_succeeded")
            if state.get("user_update") and not state.get("user_update_applied"):
                state["known"].update(state["user_update"])
                state["revision"] += 1
                state["user_update_applied"] = True
                state["messages"].append({"role": "user", "content": "出行地改为云洲，其他条件不变", "simulated": True})
                for pending in state["pending_calls"][state["next_call_index"]:]:
                    pending["cancelled"] = True
                _emit(stores, state, "state_updated", action="trusted_user_update", changed=state["user_update"], cancelled=[c["call_id"] for c in state["pending_calls"] if c.get("cancelled")])
                for pending in state["pending_calls"][state["next_call_index"]:]:
                    cancelled = _tool_result(pending, "error", error={"code": "cancelled_state_changed", "message": "trusted user update invalidated this pending request", "retryable": False})
                    pending["result"] = cancelled
                    state["observations"].append({"call_id": pending["call_id"], "name": pending["name"], "arguments": deepcopy(pending["arguments"]), "result": cancelled, "state_revision": pending["state_revision"]})
                    _emit(stores, state, "tool_result", call_id=pending["call_id"], name=pending["name"], result=cancelled)
        budget = state["budget"]
        if budget["decisions_used"] >= 6 or budget["tool_calls_started"] >= 12 or (state["mode"] == "live" and (budget["model_requests_used"] >= 6 or time.monotonic() - started >= 60)):
            return _stop(stores, state, "budget_exhausted")
        budget["decisions_used"] += 1
        if state["mode"] == "live":
            budget["model_requests_used"] += 1
        stores.save(state)
        context = build_context(state)
        write_json(stores.run_dir / "context.json", context)
        try:
            decision = policy(deepcopy(context))
            _validate_decision(decision)
        except Exception as exc:
            status = getattr(exc, "status", "provider_failed" if state["mode"] == "live" else "invalid_output")
            return _stop(stores, state, status if status in {"provider_failed", "invalid_output", "budget_exhausted"} else "provider_failed", detail=str(exc))
        _emit(stores, state, "decision", decision=decision)
        calls, output = decision["tool_calls"], decision["output"]
        if not calls:
            if output["status"] == "clarification_required":
                if not output["requested_fields"] or set(output["requested_fields"]) - set(state["unknowns"]):
                    return _stop(stores, state, "invalid_output", detail="clarification fields must be current unknowns")
            try:
                _validate_output_evidence(output, state)
            except (ValueError, TypeError, KeyError) as exc:
                return _stop(stores, state, "invalid_output", detail=str(exc))
            if output["status"] == "answered":
                output = {**output, "answer": render_answer(output, state["known"])}
            return _stop(stores, state, output["status"], output=output)
        try:
            if len(calls) > 4 or (any(c.get("name") == "create_ticket" for c in calls) and len(calls) != 1):
                raise ValueError("read batch <=4; write batch must be one write")
            if budget["tool_calls_started"] + len(calls) > 12:
                return _stop(stores, state, "budget_exhausted")
            used_ids = {o["call_id"] for o in state["observations"]}
            ids = [c.get("call_id") for c in calls]
            if len(set(ids)) != len(ids) or used_ids.intersection(ids):
                raise ValueError("call_ids must be unique in this run")
            checked = [validate_call(c, state) for c in calls]
        except (ValueError, TypeError, PermissionError) as exc:
            return _stop(stores, state, "permission_denied" if isinstance(exc, PermissionError) else "invalid_output", detail=str(exc))
        state["pending_calls"] = [{**c, "state_revision": state["revision"], "result": None} for c in checked]
        for c in state["pending_calls"]:
            if c["name"] == "create_ticket":
                c["operation_id"] = f'OP-{state["run_id"]}-1'
        state["next_call_index"] = 0
        stores.save(state)


def run_task(task_id, variant="default", mode="offline", run_id=None, root=DEFAULT_ROOT, policy=None):
    if mode not in {"offline", "live"}:
        raise ValueError("mode must be offline or live")
    task = load_task(task_id, variant)
    run_id = run_id or (task_id.lower() + "-" + str(time.time_ns()))
    run_dir = run_directory(root, run_id)
    if run_dir.exists():
        raise ValueError("run directory exists; choose a new run-id or resume")
    state = {"task_id": task_id, "run_id": run_id, "variant": variant, "mode": mode, "user_id": task["user_id"], "goal": task["goal"], "known": task["known"], "unknowns": [] if task["known"].get("trip_date") else ["trip_date"], "messages": [{"role": "user", "content": task["goal"]}], "revision": 1, "status": "running", "observations": [], "evidence_refs": [], "pending_calls": [], "next_call_index": 0, "budget": {"decisions_used": 0, "tool_calls_started": 0, "model_requests_used": 0, "attempts_by_call_id": {}}, "seq": 0, "fixture": task.get("fixture"), "faults_used": {}, "user_update": task.get("user_update"), "update_after_approval": task.get("update_after_approval"), "approval_sequence": 0}
    state["initial_tenant"] = subject(state)["tenant_id"]
    stores = Stores(run_dir)
    _emit(stores, state, "run_started", mode=mode, fixture=state["fixture"], simulated=mode == "offline")
    return _drive(stores, state, policy)


def approve_task(run_id, request_id, root=DEFAULT_ROOT):
    stores = Stores(run_directory(root, run_id))
    state = stores.load()
    request = state.get("approval_request")
    if state["status"] != "approval_required" or not request or request["request_id"] != request_id:
        raise ValueError("no matching pending approval request")
    user = subject(state)
    if user["tenant_id"] != state["initial_tenant"] or user["role"] not in {"staff", "manager"}:
        raise PermissionError("current demo user cannot approve this intent")
    state["approval"] = {**deepcopy(request), "approver_id": user["user_id"]}
    _emit(stores, state, "state_updated", action="trusted_approval", request_id=request_id)
    if state.get("update_after_approval") and not state.get("approval_update_applied"):
        update = state["update_after_approval"]
        state["known"].update(update)
        state["revision"] += 1
        state["approval_update_applied"] = True
        state["pending_calls"][state["next_call_index"]]["arguments"].update(update)
        _emit(stores, state, "state_updated", action="trusted_parameter_change", changed=update, simulated=True)
    stores.save(state)
    return {"request_id": request_id, "approved": True, "executed": False}


def resume_task(run_id, root=DEFAULT_ROOT, reply=None, policy=None, *, crash_after_remote=False):
    run_dir = run_directory(root, run_id)
    if not (run_dir / "task.sqlite").is_file():
        raise ValueError("unknown saved run")
    stores = Stores(run_dir)
    state = stores.load()
    subject(state)
    if not can_access_run(state):
        return _stop(stores, state, "permission_denied", detail="current identity cannot access saved task")
    if state["status"] not in {"clarification_required", "approval_required", "write_outcome_unknown", "running"}:
        if state["status"] == "write_succeeded":
            # A completed intent is an idempotent read, never another write.
            return read_json(run_dir / "result.json")
        raise ValueError("run is not resumable")
    if reply is not None:
        if state["status"] != "clarification_required" or not isinstance(reply, dict) or not reply or set(reply) - set(state["unknowns"]):
            raise ValueError("reply can only fill currently requested fields")
        if "trip_date" in reply:
            if not isinstance(reply["trip_date"], str) or date.fromisoformat(reply["trip_date"]).isoformat() != reply["trip_date"]:
                raise ValueError("invalid reply date")
        state["known"].update(reply)
        state["unknowns"] = [f for f in state["unknowns"] if f not in reply]
        state["revision"] += 1
        state["messages"].append({"role": "user", "content": deepcopy(reply), "trusted": True})
        _emit(stores, state, "state_updated", action="trusted_reply", changed=reply)
    elif state["status"] == "clarification_required":
        raise ValueError("resume requires a reply for missing fields")
    return _drive(stores, state, policy, crash_after_remote=crash_after_remote)
