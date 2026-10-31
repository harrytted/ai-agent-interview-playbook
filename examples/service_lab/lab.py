"""Run a loopback service or bounded, real-HTTP acceptance scenarios."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import threading
import time
from urllib import error, request

from examples.policy_agent import core
from examples.policy_agent.storage import Stores
from .service import Engine, make_server


class Client:
    def __init__(self, base, token="demo-alice", log=None):
        self.base, self.token, self.log = base, token, log

    def call(self, method, path, value=None, key=None):
        headers = {"Authorization": "Bearer " + self.token}
        if key:
            headers["Idempotency-Key"] = key
        body = None
        if value is not None:
            body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(self.base + path, body, headers, method=method)
        try:
            with request.urlopen(req, timeout=3) as response:
                code, result = response.status, json.load(response)
        except error.HTTPError as exc:
            code, result = exc.code, json.load(exc)
        if self.log is not None:
            self.log.append({"method": method, "path": path, "body": value, "code": code, "response": result})
        return code, result

    def wait(self, task_id, statuses, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            code, task = self.call("GET", "/tasks/" + task_id)
            if code != 200:
                raise AssertionError((code, task))
            if task["status"] in statuses:
                return task
            time.sleep(0.01)
        raise AssertionError("task did not reach " + str(statuses))


@contextmanager
def running(root, *, allow_faults=False, start_worker=True, crash_hook=None):
    engine = Engine(root, allow_faults=allow_faults, crash_hook=crash_hook)
    server = make_server(engine)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    if start_worker:
        engine.start()
    try:
        yield engine, "http://127.0.0.1:" + str(server.server_port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        engine.close()
        engine.export()


def run_scenario(name, output):
    folder = Path(output) / name
    folder.mkdir(parents=True, exist_ok=True)
    root, records, checks = folder / "data", [], {}
    with running(root, allow_faults=True, start_worker=name != "approval-correction") as (engine, base):
        alice, bob = Client(base, log=records), Client(base, "demo-bob", records)
        body = {"city": "海岚", "trip_date": "2026-11-12"}
        if name == "clarification-restart":
            body.pop("trip_date")
        if name in {"crash-recovery", "approval-correction"}:
            body.update(mode="ticket", amount_cny=800, reason="教学咨询")
        if name == "crash-recovery":
            body["fault"] = "after_remote_commit"
        code, accepted = alice.call("POST", "/tasks", body, "request-1")
        task_id = accepted["task"]["id"]
        checks["accepted_before_run"] = code == 202
        if name == "duplicate-isolation":
            second, replay = alice.call("POST", "/tasks", body, "request-1")
            conflict, _ = alice.call("POST", "/tasks", {**body, "city": "云洲"}, "request-1")
            hidden, _ = bob.call("GET", "/tasks/" + task_id)
            _, other = bob.call("POST", "/tasks", body, "request-1")
            checks.update(same_task=second == 200 and replay["task"]["id"] == task_id,
                          conflict=conflict == 409, owner_hidden=hidden == 404, per_owner_key=other["task"]["id"] != task_id)
            checks["answer"] = alice.wait(task_id, {"answered"})["result"]["limit_cny"] == 700
        elif name == "clarification-restart":
            waiting = alice.wait(task_id, {"clarification_required"})
            checks["not_success"] = alice.call("GET", "/metrics")[1]["task_success"] == 0
            budget = waiting["budget"]["decisions"]
        elif name == "approval-correction":
            engine.step()
            task = alice.call("GET", "/tasks/" + task_id)[1]
            old = {k: task["draft"][k] for k in ("request_id", "payload_hash")}
            alice.call("POST", "/tasks/" + task_id + "/approve", old)
            alice.call("POST", "/tasks/" + task_id + "/correct", {"city": "云洲"})
            engine.step()
            changed = alice.call("GET", "/tasks/" + task_id)[1]
            checks["old_approval_rejected"] = alice.call("POST", "/tasks/" + task_id + "/approve", old)[0] == 409
            checks["old_evidence_invalidated"] = changed["status"] == "approval_required" and changed["draft"]["payload"]["city"] == "云洲" and changed["revision"] == 2
            checks["no_write"] = not Stores(root / "business").snapshot()
            alice.call("POST", "/tasks/" + task_id + "/cancel", {})
            checks["cancelled"] = not engine.step() and alice.call("GET", "/tasks/" + task_id)[1]["status"] == "cancelled"
        elif name == "crash-recovery":
            task = alice.wait(task_id, {"approval_required"})
            approval = {k: task["draft"][k] for k in ("request_id", "payload_hash")}
            alice.call("POST", "/tasks/" + task_id + "/approve", approval)
            deadline = time.monotonic() + 3
            while not engine.stop.is_set() and time.monotonic() < deadline:
                time.sleep(0.01)
            checks["fault_persisted"] = engine.stop.is_set() and len(Stores(root / "business").snapshot()) == 1
            budget = alice.call("GET", "/tasks/" + task_id)[1]["budget"]
        elif name == "release-rollback":
            old = alice.wait(task_id, {"answered"})
            operator = Client(base, "demo-operator", records)
            policies = core.read_json(core.DATA / "policies.json")
            bad = deepcopy(policies)
            next(d for d in bad if d["document_id"] == "P17-v2")["clauses"][0]["amount_cny"] = 7000
            checks["bad_candidate_rejected"] = operator.call("POST", "/releases", {"version": "v2", "policies": bad})[0] == 422
            checks["published"] = operator.call("POST", "/releases", {"version": "v2", "policies": policies})[0] == 200
            _, new = alice.call("POST", "/tasks", body, "request-v2")
            newer = alice.wait(new["task"]["id"], {"answered"})
            checks["pinned_versions"] = old["manifest"]["release"] == "v1" and newer["manifest"]["release"] == "v2"
            checks["rollback"] = operator.call("POST", "/releases", {"version": "v1"})[0] == 200
        else:
            checks["answer"] = alice.wait(task_id, {"answered"})["result"]["limit_cny"] == 700
    if name in {"clarification-restart", "crash-recovery"}:
        with running(root) as (_, base):
            alice = Client(base, log=records)
            if name == "clarification-restart":
                before = alice.call("GET", "/tasks/" + task_id)[1]
                checks["waiting_survived"] = before["status"] == "clarification_required" and before["budget"]["decisions"] == budget
                alice.call("POST", "/tasks/" + task_id + "/reply", {"trip_date": "2026-11-12"})
                checks["continued_budget"] = alice.wait(task_id, {"answered"})["budget"]["decisions"] > budget
            else:
                unknown = alice.call("GET", "/tasks/" + task_id)[1]
                checks["unknown_not_success"] = unknown["status"] == "write_outcome_unknown"
                alice.call("POST", "/tasks/" + task_id + "/resume", {})
                done = alice.wait(task_id, {"write_succeeded"})
                checks["budget_not_reset"] = done["budget"] == budget
                checks["one_business_object"] = len(Stores(root / "business").snapshot()) == 1 and done["result"]["replayed"]
    grade = {"scenario": name, "mode": "local_http_offline_rules", "checks": checks, "passed": all(checks.values())}
    (folder / "grade.json").write_text(json.dumps(grade, ensure_ascii=False, indent=2) + "\n")
    (folder / "result.json").write_text(json.dumps({"task_id": task_id, "checks": checks}, ensure_ascii=False, indent=2) + "\n")
    for filename in ("http.jsonl", "trace.jsonl"):
        (folder / filename).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    return grade


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["serve"], nargs="?")
    parser.add_argument("--root", type=Path, default=Path(".local/service_lab/server"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--allow-faults", action="store_true")
    parser.add_argument("--crash-once", action="store_true", help="fault injection exits this process 73")
    names = ["normal", "duplicate-isolation", "clarification-restart", "approval-correction", "crash-recovery", "release-rollback"]
    parser.add_argument("--scenario", choices=["all"] + names, default="all")
    parser.add_argument("--output", type=Path, default=Path(".local/service_lab/checks"))
    args = parser.parse_args(argv)
    if args.command == "serve":
        if args.crash_once and not args.allow_faults:
            parser.error("--crash-once requires --allow-faults")
        engine = Engine(args.root, allow_faults=args.allow_faults, crash_hook=(lambda: os._exit(73)) if args.crash_once else None)
        server = make_server(engine, args.port)
        engine.start()
        signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown, daemon=True).start())
        print(json.dumps({"ready": True, "url": "http://127.0.0.1:" + str(server.server_port)}), flush=True)
        try:
            server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
            engine.close()
            engine.export()
        return 0
    output = args.output / str(time.time_ns())
    reports = [run_scenario(name, output) for name in names if args.scenario in {"all", name}]
    print(json.dumps({"output": str(output), "reports": reports, "passed": all(r["passed"] for r in reports)}, ensure_ascii=False, indent=2))
    return 0 if all(r["passed"] for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
