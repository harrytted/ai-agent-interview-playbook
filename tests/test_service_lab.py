from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from examples.policy_agent import core
from examples.policy_agent.storage import Stores, canonical
from examples.service_lab.lab import Client, run_scenario, running
from examples.service_lab.service import Engine, InjectedCrash, APIError

ROOT = Path(__file__).resolve().parents[1]
BODY = {"city": "海岚", "trip_date": "2026-11-12"}


class ServiceLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_all_bounded_real_http_scenarios(self):
        for name in ("normal", "duplicate-isolation", "clarification-restart", "approval-correction", "crash-recovery", "release-rollback", "authorization-revocation"):
            self.assertTrue(run_scenario(name, self.root)["passed"], name)

    def test_revoked_policy_family_survives_restart_and_old_release_rollback(self):
        engine = Engine(self.root)
        task, _ = engine.submit("alice", "U001", "waiting-acl", {"city": "海岚"})
        engine.step()
        engine.release({"version": "v2", "policies": core.read_json(core.DATA / "policies.json")})
        revision = engine.set_document_access("P17", [])
        engine.release({"version": "v1"})
        engine.close()
        engine = Engine(self.root)
        try:
            engine.action("alice", task["id"], "reply", {"trip_date": "2026-11-12"})
            engine.step()
            blocked = engine.get("alice", task["id"])
            self.assertEqual(blocked["status"], "access_blocked")
            self.assertEqual(blocked["manifest"]["release"], "v1")
            self.assertEqual(blocked["access_revision"], revision)
            self.assertIsNone(blocked["result"])
            # Explicit host re-grant, rather than activation, permits continuation.
            engine.set_document_access("P17", ["staff", "manager"])
            engine.action("alice", task["id"], "resume", {})
            engine.step()
            self.assertEqual(engine.get("alice", task["id"])["result"]["limit_cny"], 700)
        finally:
            engine.close()

    def test_revocation_redacts_old_answer_draft_events_and_idempotent_replay(self):
        engine = Engine(self.root)
        try:
            task_id = engine.submit("alice", "U001", "answer-before-revoke", BODY)[0]["id"]
            engine.step()
            draft_id = engine.submit("alice", "U001", "draft-before-revoke", {**BODY, "mode": "ticket"})[0]["id"]
            engine.step()
            draft = engine.get("alice", draft_id)["draft"]
            with engine.db() as db:
                task = engine._owned(db, task_id, "alice")
                engine._save(db, task, "test_sensitive_event", policy_text="restricted clause 700")
            engine.set_document_access("P17", [])
            for identifier in (task_id, draft_id):
                visible = engine.get("alice", identifier)
                self.assertEqual(visible["access_status"], "blocked")
                self.assertIsNone(visible["result"])
                self.assertIsNone(visible["draft"])
                self.assertEqual(visible["evidence"], [])
            events = engine.get("alice", task_id, events=True)
            self.assertNotIn("restricted clause", json.dumps(events))
            replay = engine.submit("alice", "U001", "answer-before-revoke", BODY)[0]
            self.assertIsNone(replay["result"])
            with self.assertRaises(APIError) as caught:
                engine.action("alice", draft_id, "approve", {k: draft[k] for k in ("request_id", "payload_hash")})
            self.assertEqual(caught.exception.code, 403)
            self.assertEqual(Stores(self.root / "business").snapshot(), [])
        finally:
            engine.close()

    def test_revocation_between_prepare_and_dispatch_stops_new_write(self):
        engine = Engine(self.root)
        try:
            task, _ = engine.submit("alice", "U001", "prepared-acl", {**BODY, "mode": "ticket"})
            engine.step()
            draft = engine.get("alice", task["id"])["draft"]
            engine.action("alice", task["id"], "approve", {k: draft[k] for k in ("request_id", "payload_hash")})
            engine.step()
            self.assertEqual(engine.get("alice", task["id"])["status"], "write_prepared")
            engine.set_document_access("P17", [])
            engine.step()
            self.assertEqual(engine.get("alice", task["id"])["status"], "access_blocked")
            self.assertEqual(Stores(self.root / "business").snapshot(), [])
        finally:
            engine.close()

    def test_unverifiable_release_never_exposes_saved_answer_or_draft(self):
        engine = Engine(self.root)
        try:
            for mode in ("query", "ticket"):
                task, _ = engine.submit("alice", "U001", "invalid-release-" + mode, {**BODY, "mode": mode})
                engine.step()
                with engine.db() as db:
                    state = engine._owned(db, task["id"], "alice")
                    state["manifest"]["index_hash"] = "not-the-recorded-release"
                    engine._save(db, state, "test_manifest_mismatch")
                visible = engine.get("alice", task["id"])
                self.assertEqual(visible["access_status"], "blocked")
                self.assertIsNone(visible["result"])
                self.assertIsNone(visible["draft"])
            with engine.db() as db:
                db.execute("DELETE FROM releases WHERE version='v1'")
            self.assertEqual(engine.get("alice", task["id"])["access_status"], "blocked")
        finally:
            engine.close()

    def test_revoked_unknown_write_reconciles_actual_object_without_disclosing_policy(self):
        engine = Engine(self.root, allow_faults=True)
        task, _ = engine.submit("alice", "U001", "unknown-acl", {**BODY, "mode": "ticket", "fault": "after_remote_commit"})
        engine.step()
        draft = engine.get("alice", task["id"])["draft"]
        engine.action("alice", task["id"], "approve", {k: draft[k] for k in ("request_id", "payload_hash")})
        engine.step()
        with self.assertRaises(InjectedCrash):
            engine.step()
        engine.set_document_access("P17", [])
        engine.close()
        engine = Engine(self.root)
        try:
            engine.action("alice", task["id"], "resume", {})
            engine.step()
            visible = engine.get("alice", task["id"])
            self.assertEqual(visible["status"], "write_succeeded")
            self.assertEqual(visible["access_status"], "blocked")
            self.assertTrue(visible["result"]["content_redacted"])
            self.assertEqual(set(visible["result"]["object"]), {"object_id", "operation_id", "tenant_id"})
            self.assertIsNone(visible["draft"])
            self.assertEqual(len(Stores(self.root / "business").snapshot()), 1)
        finally:
            engine.close()

    def test_revoked_unknown_absence_never_dispatches_a_fresh_retry(self):
        engine = Engine(self.root)
        try:
            task, _ = engine.submit("alice", "U001", "absent-acl", {**BODY, "mode": "ticket"})
            engine.step()
            draft = engine.get("alice", task["id"])["draft"]
            engine.action("alice", task["id"], "approve", {k: draft[k] for k in ("request_id", "payload_hash")})
            engine.step()
            with engine.db() as db:
                state = engine._owned(db, task["id"], "alice")
                state["status"] = "write_outcome_unknown"
                engine._save(db, state, "test_unknown_before_observation")
            engine.set_document_access("P17", [])
            engine.action("alice", task["id"], "resume", {})
            engine.step()
            self.assertEqual(engine.get("alice", task["id"])["status"], "write_outcome_unknown")
            self.assertEqual(Stores(self.root / "business").snapshot(), [])
        finally:
            engine.close()

    def test_concurrent_duplicate_acceptance_is_atomic_and_owner_scoped(self):
        with running(self.root) as (engine, base):
            def submit(_):
                return Client(base).call("POST", "/tasks", BODY, "same-intent")
            with ThreadPoolExecutor(max_workers=6) as pool:
                responses = list(pool.map(submit, range(12)))
            self.assertEqual(sum(code == 202 for code, _ in responses), 1)
            self.assertEqual(len({result["task"]["id"] for _, result in responses}), 1)
            self.assertEqual(engine.metrics("alice")["accepted"], 1)
            task_id = responses[0][1]["task"]["id"]
            bob = Client(base, "demo-bob")
            for method, suffix, value in (("GET", "", None), ("GET", "/events", None), ("POST", "/cancel", {}), ("POST", "/correct", {"city": "云洲"})):
                self.assertEqual(bob.call(method, "/tasks/" + task_id + suffix, value)[0], 404)

    def test_queued_cancel_before_worker_never_reads_or_writes(self):
        with running(self.root, start_worker=False) as (engine, base):
            client = Client(base)
            _, accepted = client.call("POST", "/tasks", {**BODY, "mode": "ticket"}, "cancel-before-start")
            task_id = accepted["task"]["id"]
            self.assertFalse((self.root / "runs").exists())
            self.assertEqual(client.call("POST", "/tasks/" + task_id + "/cancel", {})[0], 200)
            self.assertFalse(engine.step())
            task = client.call("GET", "/tasks/" + task_id)[1]
            self.assertEqual(task["budget"], {"decisions": 0, "tools": 0})
            self.assertEqual(task["status"], "cancelled")

    def test_prepared_write_cancelled_before_dispatch_creates_no_business_object(self):
        engine = Engine(self.root)
        try:
            task, _ = engine.submit("alice", "U001", "prepared", {**BODY, "mode": "ticket"})
            engine.step()
            draft = engine.get("alice", task["id"])["draft"]
            engine.action("alice", task["id"], "approve", {k: draft[k] for k in ("request_id", "payload_hash")})
            engine.step()
            self.assertEqual(engine.get("alice", task["id"])["status"], "write_prepared")
            self.assertEqual(Stores(self.root / "business").snapshot(), [])
            engine.action("alice", task["id"], "cancel", {})
            self.assertFalse(engine.step())
            self.assertEqual(Stores(self.root / "business").snapshot(), [])
            self.assertEqual(engine.get("alice", task["id"])["status"], "cancelled")
        finally:
            engine.close()

    def test_dispatch_commit_wins_cancel_race_but_result_preserves_cancel_flag(self):
        entered, release = threading.Event(), threading.Event()
        original = Stores.create
        errors = []
        def paused_create(store, *args):
            entered.set()
            if not release.wait(4):
                raise RuntimeError("dispatch barrier timed out")
            return original(store, *args)
        with running(self.root, start_worker=False) as (engine, base):
            client = Client(base)
            task_id = client.call("POST", "/tasks", {**BODY, "mode": "ticket"}, "dispatch-race")[1]["task"]["id"]
            engine.step()
            draft = client.call("GET", "/tasks/" + task_id)[1]["draft"]
            client.call("POST", "/tasks/" + task_id + "/approve", {k: draft[k] for k in ("request_id", "payload_hash")})
            engine.step()
            def dispatch():
                try:
                    engine.step()
                except Exception as exc:
                    errors.append(exc)
            with patch.object(Stores, "create", paused_create):
                worker = threading.Thread(target=dispatch)
                worker.start()
                try:
                    self.assertTrue(entered.wait(4))
                    task = client.call("GET", "/tasks/" + task_id)[1]
                    self.assertEqual(task["status"], "writing")
                    client.call("POST", "/tasks/" + task_id + "/cancel", {})
                finally:
                    release.set()
                    worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])
            task = client.call("GET", "/tasks/" + task_id)[1]
            self.assertEqual(task["status"], "cancelled")
            self.assertTrue(task["result"]["cancel_requested"])
            self.assertEqual(len(Stores(self.root / "business").snapshot()), 1)

    def test_cancelled_unknown_absence_does_not_create_or_pretend_revocation(self):
        engine = Engine(self.root)
        task, _ = engine.submit("alice", "U001", "absent-unknown", {**BODY, "mode": "ticket"})
        engine.step()
        draft = engine.get("alice", task["id"])["draft"]
        engine.action("alice", task["id"], "approve", {k: draft[k] for k in ("request_id", "payload_hash")})
        engine.step()
        state = engine.get("alice", task["id"])
        state["status"] = "writing"  # Durable dispatch, then process loss before observed remote outcome.
        with engine.db() as db:
            engine._save(db, state, "test_dispatch_committed")
        engine.close()
        restarted = Engine(self.root)
        try:
            restarted.action("alice", task["id"], "cancel", {})
            restarted.step()
            unknown = restarted.get("alice", task["id"])
            self.assertEqual(unknown["status"], "write_outcome_unknown")
            self.assertTrue(unknown["cancel_requested"])
            self.assertEqual(Stores(self.root / "business").snapshot(), [])
        finally:
            restarted.close()

    def test_cancel_after_remote_commit_reconciles_object_and_keeps_cancel_intent(self):
        committed, release = threading.Event(), threading.Event()
        def pause_after_commit():
            committed.set()
            if not release.wait(4):
                raise RuntimeError("test did not release commit barrier")
        with running(self.root, allow_faults=True, crash_hook=pause_after_commit) as (_, base):
            client = Client(base)
            _, accepted = client.call("POST", "/tasks", {**BODY, "mode": "ticket", "fault": "after_remote_commit"}, "cancel-after-write")
            task_id = accepted["task"]["id"]
            task = client.wait(task_id, {"approval_required"})
            client.call("POST", "/tasks/" + task_id + "/approve", {k: task["draft"][k] for k in ("request_id", "payload_hash")})
            self.assertTrue(committed.wait(4))
            try:
                self.assertEqual(client.call("POST", "/tasks/" + task_id + "/correct", {"amount_cny": 900})[0], 409)
                self.assertEqual(client.call("POST", "/tasks/" + task_id + "/cancel", {})[0], 200)
            finally:
                release.set()
            cancelled = client.wait(task_id, {"cancelled"})
            self.assertTrue(cancelled["result"]["cancel_requested"])
            self.assertIn("object_id", cancelled["result"]["object"])
            self.assertEqual(len(Stores(self.root / "business").snapshot()), 1)

    def test_budget_survives_revisions_and_ends_bounded_loop(self):
        with running(self.root, start_worker=False) as (engine, base):
            client = Client(base)
            task = client.call("POST", "/tasks", BODY, "budget")[1]["task"]
            for i in range(9):
                if i:
                    client.call("POST", "/tasks/" + task["id"] + "/correct", {"amount_cny": 651 + i})
                engine.step()
            final = client.call("GET", "/tasks/" + task["id"])[1]
            self.assertEqual(final["status"], "budget_exhausted")
            self.assertEqual(final["budget"]["decisions"], 8)

    def test_old_runtime_does_not_silently_resume_and_duplicate_process_rejected(self):
        engine = Engine(self.root)
        try:
            with self.assertRaises(ValueError):
                Engine(self.root)
            task, _ = engine.submit("alice", "U001", "old", BODY)
            task["manifest"]["runtime_schema"] = 99
            with engine.db() as db:
                db.execute("UPDATE tasks SET body=? WHERE id=?", (canonical(task), task["id"]))
            engine.step()
            self.assertEqual(engine.get("alice", task["id"])["status"], "blocked_version")
        finally:
            engine.close()

    def test_unauthenticated_and_malformed_requests_rejected_without_tasks(self):
        with running(self.root) as (engine, base):
            bad = Client(base, "unrecognized-test-identity")
            self.assertEqual(bad.call("POST", "/tasks", BODY, "bad")[0], 401)
            client = Client(base)
            for body in ({**BODY, "user_id": "U002"}, {**BODY, "trip_date": "tomorrow"}, {**BODY, "amount_cny": True}, {**BODY, "fault": "after_remote_commit"}, {**BODY, "city": []}, {**BODY, "city": {}}, {**BODY, "mode": []}, {**BODY, "mode": {}}):
                self.assertEqual(client.call("POST", "/tasks", body, "bad")[0], 400)
            self.assertEqual(engine.metrics("alice")["accepted"], 0)

    def test_new_release_rejects_malformed_rows_outside_fixed_smoke_queries(self):
        with running(self.root) as (_, base):
            operator = Client(base, "demo-operator")
            original = core.read_json(core.DATA / "policies.json")
            for field, value in (("valid_from", []), ("allowed_roles", [{}]), ("clauses", []), ("city", {})):
                candidate = deepcopy(original)
                candidate.append({**deepcopy(original[0]), "document_id": "malformed-extra", field: value})
                self.assertEqual(operator.call("POST", "/releases", {"version": "v2", "policies": candidate})[0], 422)

    def test_release_activation_requires_boolean_before_registering_or_switching(self):
        with running(self.root) as (engine, base):
            operator = Client(base, "demo-operator")
            policies = core.read_json(core.DATA / "policies.json")
            for value in ("false", "true", 0, 1, [], {}, None):
                with self.subTest(value=value):
                    code, _ = operator.call("POST", "/releases", {
                        "version": "v2", "policies": policies, "activate": value})
                    self.assertEqual(code, 400)
                    with engine.db() as db:
                        self.assertEqual(db.execute("SELECT value FROM settings WHERE key='active'").fetchone()[0], "v1")
                        self.assertEqual(db.execute("SELECT COUNT(*) FROM releases WHERE version='v2'").fetchone()[0], 0)
            self.assertEqual(operator.call("POST", "/releases", {
                "version": "v2", "policies": policies, "activate": False})[0], 200)
            client = Client(base)
            staged = client.call("POST", "/tasks", BODY, "before-activation")[1]["task"]
            self.assertEqual(staged["manifest"]["release"], "v1")
            self.assertEqual(operator.call("POST", "/releases", {"version": "v2", "activate": True})[0], 200)
            activated = client.call("POST", "/tasks", BODY, "after-activation")[1]["task"]
            self.assertEqual(activated["manifest"]["release"], "v2")

    def test_release_gate_uses_actual_alice_authorization_not_raw_amount_match(self):
        with running(self.root) as (_, base):
            operator = Client(base, "demo-operator")
            original = core.read_json(core.DATA / "policies.json")
            for field, value in (("allowed_roles", []), ("tenant_id", "another-tenant")):
                candidate = deepcopy(original)
                next(d for d in candidate if d["document_id"] == "P17-v2")[field] = value
                self.assertEqual(operator.call("POST", "/releases", {"version": "v2", "policies": candidate})[0], 422)

    def test_release_activation_pins_waiting_runs_and_operator_cannot_read_tasks(self):
        with running(self.root) as (_, base):
            client, operator = Client(base), Client(base, "demo-operator")
            task_id = client.call("POST", "/tasks", {"city": "海岚"}, "wait-release")[1]["task"]["id"]
            client.wait(task_id, {"clarification_required"})
            policies = core.read_json(core.DATA / "policies.json")
            self.assertEqual(client.call("POST", "/releases", {"version": "v2", "policies": policies})[0], 403)
            self.assertEqual(operator.call("POST", "/releases", {"version": "v2", "policies": policies})[0], 200)
            self.assertEqual(operator.call("GET", "/tasks/" + task_id)[0], 403)
            client.call("POST", "/tasks/" + task_id + "/reply", {"trip_date": "2026-11-12"})
            self.assertEqual(client.wait(task_id, {"answered"})["manifest"]["release"], "v1")

    def _start_process(self, crash=False):
        cmd = [sys.executable, "-m", "examples.service_lab.lab", "serve", "--root", str(self.root), "--port", "0", "--allow-faults"]
        if crash:
            cmd.append("--crash-once")
        process = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self._clean_process, process)
        ready, _, _ = select.select([process.stdout], [], [], 5)
        self.assertTrue(ready, "service readiness timed out")
        line = process.stdout.readline()
        self.assertTrue(line, "service exited before readiness")
        return process, json.loads(line)["url"]

    @staticmethod
    def _clean_process(process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()

    def test_real_process_death_after_business_commit_recovers_one_object(self):
        first, base = self._start_process(crash=True)
        client = Client(base)
        task_id = client.call("POST", "/tasks", {**BODY, "mode": "ticket", "fault": "after_remote_commit"}, "process-crash")[1]["task"]["id"]
        draft = client.wait(task_id, {"approval_required"})["draft"]
        client.call("POST", "/tasks/" + task_id + "/approve", {k: draft[k] for k in ("request_id", "payload_hash")})
        self.assertEqual(first.wait(timeout=5), 73)
        self.assertEqual(len(Stores(self.root / "business").snapshot()), 1)
        second, base = self._start_process()
        client = Client(base)
        unknown = client.call("GET", "/tasks/" + task_id)[1]
        self.assertEqual(unknown["status"], "write_outcome_unknown")
        budget = deepcopy(unknown["budget"])
        client.call("POST", "/tasks/" + task_id + "/resume", {})
        done = client.wait(task_id, {"write_succeeded"})
        self.assertEqual(done["budget"], budget)
        self.assertTrue(done["result"]["replayed"])
        self.assertEqual(len(Stores(self.root / "business").snapshot()), 1)
        second.terminate()
        self.assertEqual(second.wait(timeout=5), 0)


if __name__ == "__main__":
    unittest.main()
