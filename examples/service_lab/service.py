"""Teaching HTTP service. Public demo tokens are test identities, not secrets.

One POSIX process owns each root; SQLite serializes API and worker transitions.
The independent business store deliberately exposes the commit/ack gap.
"""
from __future__ import annotations

from copy import deepcopy
from contextlib import contextmanager
from datetime import date
import fcntl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
import threading
import time
from urllib.parse import urlsplit
import uuid

from examples.policy_agent import core
from examples.policy_agent.storage import Stores, canonical, fingerprint

TOKENS = {"demo-alice": ("alice", "U001"), "demo-bob": ("bob", "U002")}
PROMPT = "Read applicable authorized lodging policy; never infer reimbursement approval."
TOOL_CONTRACT = {"read": "authorized policy by business date", "write": "approved consultation draft v1"}
TERMINAL = {"answered", "write_succeeded", "cancelled", "insufficient_evidence", "budget_exhausted", "blocked_version"}


class APIError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class InjectedCrash(RuntimeError):
    pass


def validate_spec(value, partial=False):
    allowed = {"city", "trip_date", "amount_cny", "reason", "mode", "fault"}
    if not isinstance(value, dict) or set(value) - allowed:
        raise APIError(400, "unknown task fields")
    if not partial and ("city" not in value or not isinstance(value.get("mode", "query"), str) or value.get("mode", "query") not in {"query", "ticket"}):
        raise APIError(400, "city and query/ticket mode required")
    if "city" in value and (not isinstance(value["city"], str) or value["city"] not in {"海岚", "云洲"}):
        raise APIError(400, "city must be 海岚 or 云洲")
    if "trip_date" in value:
        try:
            if not isinstance(value["trip_date"], str) or date.fromisoformat(value["trip_date"]).isoformat() != value["trip_date"]:
                raise ValueError()
        except ValueError:
            raise APIError(400, "trip_date must be an ISO business date") from None
    if "amount_cny" in value and (type(value["amount_cny"]) is not int or not 0 <= value["amount_cny"] <= 100_000):
        raise APIError(400, "amount_cny must be an integer from 0 to 100000")
    if "reason" in value and (not isinstance(value["reason"], str) or not 1 <= len(value["reason"]) <= 200):
        raise APIError(400, "reason must have 1 to 200 characters")
    if "fault" in value and value["fault"] != "after_remote_commit":
        raise APIError(400, "unknown fault")
    return deepcopy(value)


class Engine:
    def __init__(self, root, *, allow_faults=False, crash_hook=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock_file = (self.root / ".worker.lock").open("a")
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock_file.close()
            raise ValueError("one service process may own a data root") from None
        self.allow_faults = allow_faults
        self.crash_hook = crash_hook or self._injected_crash
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.worker = None
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, owner TEXT NOT NULL, idem TEXT NOT NULL,
                    request_hash TEXT NOT NULL, body TEXT NOT NULL, UNIQUE(owner,idem));
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS releases (
                    version TEXT PRIMARY KEY, manifest TEXT NOT NULL, policies TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)
            if not db.execute("SELECT 1 FROM releases LIMIT 1").fetchone():
                policies = core.read_json(core.DATA / "policies.json")
                self._insert_release(db, "v1", policies)
                db.execute("INSERT INTO settings VALUES ('active','v1')")
            for row in db.execute("SELECT id,body FROM tasks").fetchall():
                task = json.loads(row["body"])
                if task["status"] in {"writing", "reconciling"}:
                    task["status"] = "write_outcome_unknown"
                    self._save(db, task, "restart_requires_reconciliation")

    @staticmethod
    def _injected_crash():
        raise InjectedCrash("fault after business commit, before task acknowledgment")

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.root / "tasks.sqlite", timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _insert_release(self, db, version, policies):
        manifest = {"runtime_schema": 1, "model": "offline-policy-rules-v1", "prompt_hash": fingerprint(PROMPT),
                    "tool_hash": fingerprint(TOOL_CONTRACT), "index_hash": fingerprint(policies), "release": version}
        db.execute("INSERT INTO releases VALUES (?,?,?)", (version, canonical(manifest), canonical(policies)))
        return manifest

    def _save(self, db, task, event, **details):
        db.execute("UPDATE tasks SET body=? WHERE id=?", (canonical(task), task["id"]))
        db.execute("INSERT INTO events(task_id,body) VALUES (?,?)", (task["id"], canonical({"event": event, "revision": task["revision"], "status": task["status"], "at": time.time(), **details})))

    def _owned(self, db, task_id, owner):
        row = db.execute("SELECT body FROM tasks WHERE id=? AND owner=?", (task_id, owner)).fetchone()
        if not row:
            raise APIError(404, "task not found")
        return json.loads(row["body"])

    def submit(self, owner, user_id, idem, value):
        spec = validate_spec(value)
        if "fault" in spec and not self.allow_faults:
            raise APIError(400, "fault injection disabled")
        spec.setdefault("mode", "query")
        if not isinstance(idem, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", idem):
            raise APIError(400, "Idempotency-Key required (1-80 ASCII identifier characters)")
        digest = fingerprint(spec)
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT request_hash,body FROM tasks WHERE owner=? AND idem=?", (owner, idem)).fetchone()
            if row:
                if row["request_hash"] != digest:
                    raise APIError(409, "same key with different initial request")
                return json.loads(row["body"]), True
            release = db.execute("SELECT value FROM settings WHERE key='active'").fetchone()[0]
            manifest = json.loads(db.execute("SELECT manifest FROM releases WHERE version=?", (release,)).fetchone()[0])
            task_id = uuid.uuid4().hex
            task = {"id": task_id, "run_id": "run-" + task_id, "owner": owner, "user_id": user_id,
                    "spec": spec, "status": "queued", "revision": 1, "budget": {"decisions": 0, "tools": 0},
                    "manifest": manifest, "evidence": [], "result": None, "draft": None, "approval": None,
                    "cancel_requested": False, "fault_used": False, "operation_id": "OP-" + task_id}
            db.execute("INSERT INTO tasks VALUES (?,?,?,?,?)", (task_id, owner, idem, digest, canonical(task)))
            self._save(db, task, "accepted", initial_request_hash=digest)
        # No run directory or execution exists before the acceptance transaction commits.
        self.wake.set()
        return task, False

    def get(self, owner, task_id, events=False):
        with self.db() as db:
            task = self._owned(db, task_id, owner)
            if events:
                return [{"seq": row["seq"], **json.loads(row["body"])} for row in db.execute("SELECT seq,body FROM events WHERE task_id=? ORDER BY seq", (task_id,))]
            return task

    def action(self, owner, task_id, action, value):
        if not isinstance(value, dict):
            raise APIError(400, "action body must be an object")
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            task = self._owned(db, task_id, owner)
            if action in {"reply", "correct"}:
                if task["status"] in {"writing", "reconciling", "write_outcome_unknown", "write_succeeded", "cancelled", "blocked_version"}:
                    raise APIError(409, "cannot revise a submitted write or closed task")
                if action == "reply" and task["status"] != "clarification_required":
                    raise APIError(409, "task is not waiting for clarification")
                if set(value) - ({"trip_date"} if action == "reply" else {"city", "trip_date", "amount_cny", "reason"}) or not value:
                    raise APIError(400, "unsupported correction fields")
                validate_spec(value, partial=True)
                task["spec"].update(value)
                task.update(revision=task["revision"] + 1, status="queued", approval=None, draft=None, evidence=[], result=None)
            elif action == "approve":
                if task["status"] != "approval_required" or set(value) != {"request_id", "payload_hash"}:
                    raise APIError(409, "a current approval request is required")
                if value != {key: task["draft"][key] for key in ("request_id", "payload_hash")}:
                    raise APIError(409, "approval no longer matches this draft")
                task["approval"] = {**value, "owner": owner, "revision": task["revision"]}
                task["status"] = "queued"
            elif action == "cancel":
                if value:
                    raise APIError(400, "cancel body must be empty")
                if task["status"] == "write_succeeded":
                    raise APIError(409, "completed write requires a separate authorized compensation")
                if task["status"] != "cancelled":
                    task["cancel_requested"] = True
                    if task["status"] not in {"writing", "reconciling", "write_outcome_unknown"}:
                        task.update(status="cancelled", revision=task["revision"] + 1, evidence=[], result=None, approval=None, draft=None)
                    elif task["status"] == "write_outcome_unknown":
                        task["status"] = "reconciling"  # Lookup only after cancellation.
            elif action == "resume":
                if value or task["status"] not in {"write_outcome_unknown", "queued"}:
                    raise APIError(409, "nothing resumable without new input")
                if task["manifest"]["runtime_schema"] != 1:
                    raise APIError(409, "runtime schema requires explicit migration")
                task["status"] = "reconciling" if task["status"] == "write_outcome_unknown" else "queued"
            else:
                raise APIError(404, "unknown task action")
            self._save(db, task, "user_" + action)
        self.wake.set()
        return task

    def _evidence(self, db, task):
        row = db.execute("SELECT policies,manifest FROM releases WHERE version=?", (task["manifest"]["release"],)).fetchone()
        if not row or json.loads(row["manifest"]) != task["manifest"]:
            return None
        user = {"user_id": task["user_id"], **core.read_json(core.USER_FILE)[task["user_id"]]}
        state = {"known": {"trip_date": task["spec"]["trip_date"]}}
        return [d for d in json.loads(row["policies"]) if d["topic"] == "lodging" and d["city"] == task["spec"]["city"] and core.applicable(d, state, user)]

    def step(self):
        writing = None
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            tasks = [json.loads(row[0]) for row in db.execute("SELECT body FROM tasks ORDER BY rowid")]
            task = next((t for t in tasks if t["status"] in {"queued", "write_prepared", "reconciling"}), None)
            if task is None:
                return False
            folder = self.root / "runs" / task["run_id"]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "manifest.json").write_text(json.dumps(task["manifest"], ensure_ascii=False, indent=2) + "\n")
            if task["manifest"]["runtime_schema"] != 1:
                task["status"] = "blocked_version"
                self._save(db, task, "incompatible_runtime")
            elif task["status"] == "write_prepared":
                # The transaction commit below is the local dispatch boundary.
                # Cancellation/correction that commits before it prevents dispatch.
                if task["budget"]["tools"] >= 12:
                    task["status"] = "budget_exhausted"
                    self._save(db, task, "dispatch_budget_stopped")
                    return True
                task["status"] = "writing"
                task["budget"]["tools"] += 1
                writing = {**deepcopy(task), "new_dispatch": True}
                if task["spec"].get("fault") and not task["fault_used"]:
                    task["fault_used"] = True
                    writing["inject_crash"] = True
                self._save(db, task, "dispatch_committed")
            elif task["status"] == "reconciling":
                writing = {**deepcopy(task), "new_dispatch": False}
            elif task["budget"]["decisions"] >= 8 or task["budget"]["tools"] >= 12:
                task["status"] = "budget_exhausted"
                self._save(db, task, "budget_stopped")
            else:
                task["budget"]["decisions"] += 1
                if "trip_date" not in task["spec"]:
                    task["status"] = "clarification_required"
                    self._save(db, task, "needs_trip_date")
                else:
                    evidence = self._evidence(db, task)
                    if evidence is None:
                        task["status"] = "blocked_version"
                    elif len(evidence) != 1:
                        task["status"] = "insufficient_evidence"
                    elif task["approval"]:
                        approval, draft = task["approval"], task["draft"]
                        if (approval["revision"] != task["revision"] or approval["owner"] != task["owner"]
                                or fingerprint(draft["payload"]) != approval["payload_hash"]):
                            task.update(status="approval_required", approval=None)
                        else:
                            task["status"] = "write_prepared"
                    else:
                        task["budget"]["tools"] += 1
                        document = evidence[0]
                        clause = next(c for c in document["clauses"] if "amount_cny" in c)
                        task["evidence"] = [{"reference": clause["clause_id"], "document_id": document["document_id"], "revision": task["revision"]}]
                        result = {"city": task["spec"]["city"], "trip_date": task["spec"]["trip_date"], "limit_cny": clause["amount_cny"], "reference": clause["clause_id"], "revision": task["revision"]}
                        if task["spec"]["mode"] == "query":
                            task.update(status="answered", result=result)
                        else:
                            payload = {**result, "amount_cny": task["spec"].get("amount_cny", 650), "reason": task["spec"].get("reason", "政策例外咨询")}
                            task["draft"] = {"request_id": "APR-" + task["id"] + "-" + str(task["revision"]), "payload": payload, "payload_hash": fingerprint(payload)}
                            task["status"] = "approval_required"
                    self._save(db, task, "worker_transition")
        if writing:
            # No task transaction spans the business-store transaction. A crash can
            # occur here; reconciliation uses the same operation ID and full payload.
            store = Stores(self.root / "business")
            current_user = core.read_json(core.USER_FILE)[writing["user_id"]]
            if current_user["tenant_id"] != "demo-a" or current_user["role"] not in {"staff", "manager"}:
                raise ValueError("current test identity no longer authorized")
            ticket = store.lookup(current_user["tenant_id"], writing["operation_id"])
            replayed = ticket is not None
            if ticket is not None:
                payload = writing["draft"]["payload"]
                if fingerprint({key: ticket.get(key) for key in payload}) != fingerprint(payload):
                    raise ValueError("business reconciliation content conflict")
            elif writing["new_dispatch"]:
                ticket, replayed = store.create(current_user["tenant_id"], writing["operation_id"], writing["draft"]["payload"])
            else:
                with self.db() as db:
                    db.execute("BEGIN IMMEDIATE")
                    current = self._owned(db, writing["id"], writing["owner"])
                    if current["cancel_requested"]:
                        # Absence is not proof the old request cannot still commit.
                        current["status"] = "write_outcome_unknown"
                        current["result"] = {"object": None, "cancel_requested": True, "detail": "lookup absent; dispatched outcome remains unknown"}
                        self._save(db, current, "reconciliation_still_unknown")
                        return True
                    # An uncancelled idempotent retry has its own serialized
                    # dispatch boundary, without a fresh logical tool budget.
                    current["status"] = "writing"
                    self._save(db, current, "retry_dispatch_committed")
                ticket, replayed = store.create(current_user["tenant_id"], writing["operation_id"], writing["draft"]["payload"])
            if writing.get("inject_crash"):
                self.crash_hook()
            with self.db() as db:
                db.execute("BEGIN IMMEDIATE")
                current = self._owned(db, writing["id"], writing["owner"])
                current["result"] = {"object": ticket, "replayed": replayed, "cancel_requested": current["cancel_requested"]}
                current["status"] = "cancelled" if current["cancel_requested"] else "write_succeeded"
                self._save(db, current, "business_acknowledged", object_id=ticket["object_id"])
        return True

    def start(self):
        if self.worker is not None:
            return
        def loop():
            try:
                while not self.stop.is_set():
                    if not self.step():
                        self.wake.wait(0.05)
                        self.wake.clear()
            except Exception as exc:
                self.worker_error = type(exc).__name__
                self.stop.set()
        self.worker_error = None
        self.worker = threading.Thread(target=loop, name="single-task-worker", daemon=True)
        self.worker.start()

    def close(self):
        self.stop.set()
        self.wake.set()
        if self.worker:
            self.worker.join(timeout=5)
            if self.worker.is_alive():
                raise RuntimeError("worker did not drain within local deadline")
        fcntl.flock(self.lock_file, fcntl.LOCK_UN)
        self.lock_file.close()

    def release(self, value):
        if not isinstance(value, dict) or set(value) - {"version", "policies", "activate"} or not isinstance(value.get("version"), str) or not re.fullmatch(r"v[0-9]+", value["version"]):
            raise APIError(400, "release version must be v<number>")
        if "activate" in value and type(value["activate"]) is not bool:
            raise APIError(400, "activate must be a JSON boolean")
        version = value["version"]
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if "policies" in value:
                policies = value["policies"]
                # A fixed, independent smoke gate; not proof of general RAG quality.
                expected = {("海岚", "staff", "2026-11-12"): 700, ("海岚", "staff", "2026-10-12"): 600, ("云洲", "staff", "2026-11-12"): 650}
                try:
                    if not isinstance(policies, list) or not policies:
                        raise ValueError()
                    ids = set()
                    for document in policies:
                        if not isinstance(document, dict):
                            raise ValueError()
                        for field in ("document_id", "policy_id", "topic", "tenant_id", "city", "employee_category", "valid_from"):
                            if not isinstance(document.get(field), str):
                                raise ValueError()
                        if not document["document_id"] or document["document_id"] in ids:
                            raise ValueError()
                        ids.add(document["document_id"])
                        if date.fromisoformat(document["valid_from"]).isoformat() != document["valid_from"]:
                            raise ValueError()
                        if document.get("valid_to") is not None:
                            if date.fromisoformat(document["valid_to"]).isoformat() != document["valid_to"]:
                                raise ValueError()
                            if document["valid_to"] <= document["valid_from"]:
                                raise ValueError()
                        if not isinstance(document.get("allowed_roles"), list) or any(not isinstance(role, str) or not role or len(role) > 64 for role in document["allowed_roles"]):
                            raise ValueError()
                        if not isinstance(document.get("clauses"), list) or not document["clauses"]:
                            raise ValueError()
                        for clause in document["clauses"]:
                            if not isinstance(clause, dict) or not isinstance(clause.get("clause_id"), str) or not isinstance(clause.get("text"), str):
                                raise ValueError()
                            if "amount_cny" in clause and (type(clause["amount_cny"]) is not int or clause["amount_cny"] < 0):
                                raise ValueError()
                        if document["topic"] == "lodging" and not any("amount_cny" in c for c in document["clauses"]):
                            raise ValueError()
                    alice = {"user_id": "U001", **core.read_json(core.USER_FILE)["U001"]}
                    for (city, category, day), amount in expected.items():
                        state = {"known": {"trip_date": day}}
                        matches = [d for d in policies if d["topic"] == "lodging" and d["city"] == city and d["employee_category"] == category and core.applicable(d, state, alice)]
                        if len(matches) != 1 or matches[0]["clauses"][0]["amount_cny"] != amount:
                            raise ValueError()
                    if any(not isinstance(d["tenant_id"], str) or not isinstance(d["allowed_roles"], list) for d in policies):
                        raise ValueError()
                except (KeyError, IndexError, TypeError, ValueError):
                    raise APIError(422, "candidate fails fixed policy/metadata gate") from None
                if db.execute("SELECT 1 FROM releases WHERE version=?", (version,)).fetchone():
                    raise APIError(409, "release versions are immutable")
                self._insert_release(db, version, policies)
            row = db.execute("SELECT manifest FROM releases WHERE version=?", (version,)).fetchone()
            if not row:
                raise APIError(404, "unknown release")
            if value.get("activate", True):
                db.execute("UPDATE settings SET value=? WHERE key='active'", (version,))
            return json.loads(row[0])

    def metrics(self, owner):
        with self.db() as db:
            states = [json.loads(r[0]) for r in db.execute("SELECT body FROM tasks WHERE owner=?", (owner,))]
        return {"accepted": len(states), "task_success": sum(t["status"] in {"answered", "write_succeeded"} for t in states),
                "waiting": sum(t["status"] in {"clarification_required", "approval_required", "write_outcome_unknown"} for t in states),
                "queued": sum(t["status"] == "queued" for t in states), "worker_ready": not self.stop.is_set(),
                "decisions": sum(t["budget"]["decisions"] for t in states)}

    def export(self):
        with self.db() as db:
            tasks = [json.loads(r[0]) for r in db.execute("SELECT body FROM tasks")]
        for task in tasks:
            folder = self.root / "runs" / task["run_id"]
            folder.mkdir(parents=True, exist_ok=True)
            events = self.get(task["owner"], task["id"], events=True)
            (folder / "trace.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events))
            (folder / "result.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n")
            (folder / "manifest.json").write_text(json.dumps(task["manifest"], indent=2) + "\n")


def make_server(engine, port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def handle_api(self):
            path = urlsplit(self.path).path
            if self.command == "GET" and path == "/health":
                ready = engine.worker is not None and engine.worker.is_alive() and not engine.stop.is_set()
                return (200 if ready else 503), {"ready": ready, "worker_error": getattr(engine, "worker_error", None)}
            authorization = self.headers.get("Authorization", "")
            token = authorization[7:] if authorization.startswith("Bearer ") else ""
            if token not in TOKENS and token != "demo-operator":
                raise APIError(401, "use an explicit public demo identity")
            value = {}
            if self.command == "POST":
                if self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json":
                    raise APIError(400, "application/json required")
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 65_536:
                        raise ValueError()
                    value = json.loads(self.rfile.read(length))
                except (ValueError, UnicodeError):
                    raise APIError(400, "invalid or oversized JSON body") from None
            if path == "/releases" and self.command == "POST":
                if token != "demo-operator":
                    raise APIError(403, "operator test identity required")
                return 200, engine.release(value)
            if token == "demo-operator":
                raise APIError(403, "operator cannot read user tasks")
            owner, user_id = TOKENS[token]
            if path == "/metrics" and self.command == "GET":
                return 200, engine.metrics(owner)
            if path == "/tasks" and self.command == "POST":
                task, replayed = engine.submit(owner, user_id, self.headers.get("Idempotency-Key"), value)
                return (200 if replayed else 202), {"task": task, "replayed": replayed}
            match = re.fullmatch(r"/tasks/([a-f0-9]{32})(?:/([a-z]+))?", path)
            if not match:
                raise APIError(404, "unknown endpoint")
            task_id, action = match.groups()
            if self.command == "GET" and action in {None, "events"}:
                return 200, engine.get(owner, task_id, events=action == "events")
            if self.command == "POST" and action:
                return 200, engine.action(owner, task_id, action, value)
            raise APIError(404, "unknown method/endpoint")

        def respond(self):
            self.connection.settimeout(3)
            try:
                code, value = self.handle_api()
            except APIError as exc:
                code, value = exc.code, {"error": str(exc)}
            except (OSError, sqlite3.Error):
                code, value = 503, {"error": "local service unavailable"}
            body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = respond
        do_POST = respond
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
