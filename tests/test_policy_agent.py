"""Behavioral and adversarial checks for the offline policy lesson."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from examples.policy_agent import core, policies
from examples.policy_agent.__main__ import evaluate
from examples.policy_agent.date_boundary import business_date
from examples.policy_agent.grade import grade
from examples.policy_agent.storage import Stores


class PolicyAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_task(self, task="T01", variant="default", **kwargs):
        return core.run_task(task, variant, run_id="demo", root=self.root, **kwargs)

    def stores(self):
        return Stores(self.root / "demo")

    def events(self):
        return [json.loads(line) for line in (self.root / "demo" / "trace.jsonl").read_text().splitlines()]

    def test_full_oracle_suite_includes_twenty_two_outcomes(self):
        report = evaluate("all", root=self.root)
        self.assertEqual((report["total"], report["passed"]), (22, 22))

    def test_rules_respond_to_changed_observation_in_same_task(self):
        self.run_task()
        view = core.build_context(self.stores().load())
        first = policies.decide(view)
        changed = deepcopy(view)
        changed["evidence"][0]["clauses"][0]["amount_cny"] = 500
        second = policies.decide(changed)
        self.assertEqual(first["output"]["claims"][0]["amount_cny"], 700)
        self.assertEqual(second["output"]["claims"][0]["amount_cny"], 500)
        changed["evidence"] = []
        changed["observations"][0]["result"]["status"] = "stale_evidence"
        recovery = policies.decide(changed)
        self.assertEqual(recovery["tool_calls"][0]["name"], "get_policy")

    def test_equivalent_claim_order_is_not_rejected_by_grader(self):
        def reversed_claims(view):
            decision = policies.decide(view)
            if decision["output"] and decision["output"]["status"] == "answered":
                decision["output"]["claims"].reverse()
            return decision
        result = self.run_task("T05", policy=reversed_claims)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["output"]["claims"][0]["city"], "云洲")
        self.assertTrue(grade(self.root / "demo")["passed"])

    def test_valid_policy_for_unrequested_date_cannot_change_the_question(self):
        def change_date(view):
            decision = policies.decide(view)
            if decision["output"] and decision["output"]["status"] == "answered":
                decision["output"]["claims"][0]["trip_date"] = "2026-11-13"
            return decision
        result = self.run_task(policy=change_date)
        self.assertEqual(result["status"], "invalid_output")
        self.assertFalse(grade(self.root / "demo")["passed"])

    def test_task_id_renaming_does_not_change_policy_behavior(self):
        original = core.load_task("T01")
        with patch.object(core, "load_task", return_value=original):
            result = core.run_task("renamed-no-answer-hint", run_id="demo", root=self.root)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["output"]["claims"][0]["amount_cny"], 700)
        view = core.build_context(self.stores().load())
        for hidden in ("task_id", "run_id", "variant", "fixture", "expected", "user_update"):
            self.assertNotIn(hidden, view)

    def test_missing_date_has_no_tools_and_cumulative_resume_budget(self):
        waiting = self.run_task(variant="missing-date")
        self.assertEqual(waiting["status"], "clarification_required")
        self.assertEqual(waiting["budget"]["tool_calls_started"], 0)
        self.assertNotIn("2026-11-12", core.build_context(self.stores().load())["goal"])
        result = core.resume_task("demo", root=self.root, reply={"trip_date": "2026-11-12"})
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["budget"]["decisions_used"], 3)
        self.assertEqual([e["seq"] for e in self.events()], list(range(1, 10)))

    def test_resume_cannot_reset_exhausted_budget(self):
        self.run_task(variant="missing-date")
        state = self.stores().load()
        state["budget"]["decisions_used"] = 6
        self.stores().save(state)
        result = core.resume_task("demo", root=self.root, reply={"trip_date": "2026-11-12"})
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["budget"]["tool_calls_started"], 0)

    def test_trusted_reply_does_not_accept_identity_or_approval_fields(self):
        self.run_task(variant="missing-date")
        for reply in ({"user_id": "U002"}, {"approved": True}, {"trip_date": "bad"}, {"trip_date": "2026-11-12", "role": "manager"}):
            with self.subTest(reply=reply), self.assertRaises(ValueError):
                core.resume_task("demo", root=self.root, reply=reply)
        self.assertEqual(self.stores().load()["user_id"], "U001")

    def test_overlarge_mixed_or_invalid_batches_execute_nothing(self):
        valid = {"call_id": "c1", "name": "search_policy", "arguments": {"query": "lodging", "city": "海岚", "trip_date": "2026-11-12"}}
        batches = [[valid, {"call_id": "c2", "name": "unknown", "arguments": {}}], [{**valid, "call_id": str(i)} for i in range(5)], [valid, deepcopy(valid)], [{**valid, "arguments": {**valid["arguments"], "approved": True}}]]
        for i, calls in enumerate(batches):
            result = core.run_task("T01", run_id=f"invalid-{i}", root=self.root, policy=lambda _v, c=calls: {"tool_calls": c, "output": None})
            self.assertEqual(result["status"], "invalid_output")
            self.assertEqual(result["budget"]["tool_calls_started"], 0)

    def test_schema_valid_but_forbidden_second_read_rejects_entire_batch(self):
        calls = [{"call_id": "c1", "name": "search_policy", "arguments": {"query": "lodging", "city": "海岚", "trip_date": "2026-11-12"}}, {"call_id": "c2", "name": "get_policy", "arguments": {"policy_id": "P21", "trip_date": "2026-11-12"}}]
        result = self.run_task(policy=lambda _v: {"tool_calls": calls, "output": None})
        self.assertEqual(result["status"], "permission_denied")
        self.assertEqual(result["budget"]["tool_calls_started"], 0)

    def test_stale_version_is_observed_but_not_used_as_current_evidence(self):
        result = self.run_task(variant="stale-first")
        self.assertEqual(result["status"], "answered")
        observations = self.stores().load()["observations"]
        self.assertEqual([o["name"] for o in observations], ["search_policy", "get_policy"])
        self.assertEqual(observations[0]["result"]["data"]["documents"][0]["clauses"][0]["amount_cny"], 600)
        self.assertEqual(result["evidence_refs"], ["P17-v2#4"])

    def test_unobserved_correct_reference_cannot_pass_runtime(self):
        output = policies.finish("answered", claims=[{"kind": "lodging_limit", "city": "海岚", "trip_date": "2026-11-12", "amount_cny": 700, "document_id": "P17-v2", "clause_id": "P17-v2#4"}], refs=["P17-v2#4"])
        result = self.run_task(policy=lambda _v: output)
        self.assertEqual(result["status"], "invalid_output")

    def test_user_correction_cancels_dependent_pending_read_and_records_result(self):
        first = True
        def policy(view):
            nonlocal first
            if first:
                first = False
                return {"tool_calls": [{"call_id": "call-1", "name": "search_policy", "arguments": {"query": "lodging", "city": "海岚", "trip_date": "2026-11-12"}}, {"call_id": "call-2", "name": "get_policy", "arguments": {"policy_id": "P17", "trip_date": "2026-11-12"}}], "output": None}
            return policies.decide(view)
        result = self.run_task("T08", policy=policy)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["output"]["claims"][0]["city"], "云洲")
        self.assertFalse(any(e["event"] == "tool_started" and e["call_id"] == "call-2" for e in self.events()))
        cancelled = [e for e in self.events() if e["event"] == "tool_result" and e["call_id"] == "call-2"]
        self.assertEqual(cancelled[0]["result"]["error"]["code"], "cancelled_state_changed")
        self.assertEqual(result["evidence_refs"], ["P19-v1#4"])

    def test_transient_read_consumes_attempts_but_one_logical_call(self):
        result = self.run_task(variant="read-transient")
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["budget"]["tool_calls_started"], 1)
        self.assertEqual(result["budget"]["attempts_by_call_id"], {"call-1": 2})

    def test_always_read_substitute_is_stopped_at_budget(self):
        result = self.run_task(variant="loop")
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["budget"]["decisions_used"], 6)
        self.assertEqual(result["budget"]["tool_calls_started"], 6)

    def test_untrusted_document_remains_data_and_does_not_trigger_finance_read(self):
        result = self.run_task(variant="untrusted-instruction")
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["output"]["claims"][0]["amount_cny"], 700)
        self.assertFalse(any(e["event"] == "tool_started" and e["arguments"].get("policy_id") == "P21" for e in self.events()))

    def test_full_payload_change_invalidates_prior_approval(self):
        result = self.run_task("T11", "parameter-changed")
        self.assertEqual(result["status"], "approval_required")
        core.approve_task("demo", result["approval_request"]["request_id"], self.root)
        result = core.resume_task("demo", self.root)
        self.assertEqual(result["status"], "approval_required")
        self.assertEqual(result["approval_request"]["payload"]["amount_cny"], 800)
        self.assertEqual(result["approval_request"]["request_id"], "APR-demo-2")
        self.assertEqual(self.stores().snapshot(), [])

    def test_approve_saves_decision_without_executing_and_completion_is_idempotent(self):
        result = self.run_task("T11")
        approval = core.approve_task("demo", result["approval_request"]["request_id"], self.root)
        self.assertFalse(approval["executed"])
        self.assertEqual(self.stores().snapshot(), [])
        completed = core.resume_task("demo", self.root)
        repeated = core.resume_task("demo", self.root)
        self.assertEqual(completed, repeated)
        self.assertEqual(len(self.stores().snapshot()), 1)
        self.assertTrue(grade(self.root / "demo")["passed"])

    def test_current_permission_is_reloaded_before_resumed_write(self):
        users = core.read_json(core.USER_FILE)
        user_file = self.root / "users.json"
        core.write_json(user_file, users)
        with patch.object(core, "USER_FILE", user_file):
            waiting = self.run_task("T11")
            core.approve_task("demo", waiting["approval_request"]["request_id"], self.root)
            users["U001"]["role"] = "revoked"
            core.write_json(user_file, users)
            result = core.resume_task("demo", self.root)
        self.assertEqual(result["status"], "permission_denied")
        self.assertEqual(self.stores().snapshot(), [])
        self.assertEqual(core.read_json(self.root / "demo" / "context.json")["evidence"], [])

    def test_fake_service_deduplicates_full_payload_and_rejects_id_reuse(self):
        service = self.stores()
        original, replayed = service.create("demo-a", "one", {"title": "A", "amount_cny": 650})
        repeated, replayed = service.create("demo-a", "one", {"title": "A", "amount_cny": 650})
        self.assertTrue(replayed)
        self.assertEqual(original["object_id"], repeated["object_id"])
        with self.assertRaises(ValueError):
            service.create("demo-a", "one", {"title": "A", "amount_cny": 800})
        self.assertIsNone(service.lookup("demo-b", "one"))
        self.assertEqual(len(service.snapshot()), 1)

    def test_recovery_uses_original_operation_after_lost_ack(self):
        waiting = self.run_task("T12")
        core.approve_task("demo", waiting["approval_request"]["request_id"], self.root)
        lost = core.resume_task("demo", self.root)
        self.assertEqual(lost["status"], "write_outcome_unknown")
        recovered = core.resume_task("demo", self.root)
        self.assertEqual(recovered["status"], "write_succeeded")
        self.assertEqual(recovered["operation_id"], "OP-demo-1")
        self.assertEqual(len(self.stores().snapshot()), 1)

    def test_unknown_write_reconciliation_cannot_bypass_budget_by_resuming(self):
        waiting = self.run_task("T12")
        core.approve_task("demo", waiting["approval_request"]["request_id"], self.root)
        self.assertEqual(core.resume_task("demo", self.root)["status"], "write_outcome_unknown")
        with self.stores().service_db() as db:
            db.execute("DELETE FROM tickets")  # Simulated authoritative absence.
        for _ in range(2):
            self.assertEqual(core.resume_task("demo", self.root)["status"], "write_outcome_unknown")
        stopped = core.resume_task("demo", self.root)
        self.assertEqual(stopped["status"], "budget_exhausted")
        self.assertEqual(stopped["budget"]["attempts_by_call_id"]["call-2-reconcile"], 2)

    def test_grader_rejects_tampered_amount_even_with_fluent_answer(self):
        self.run_task()
        path = self.root / "demo" / "result.json"
        result = core.read_json(path)
        result["output"]["claims"][0]["amount_cny"] = 999
        result["output"]["answer"] = "任务完美完成"
        core.write_json(path, result)
        self.assertFalse(grade(self.root / "demo")["passed"])

    def test_host_recomputes_displayed_comparison_from_verified_facts(self):
        def malicious_prose(view):
            decision = policies.decide(view)
            if decision["output"] and decision["output"]["status"] == "answered":
                decision["output"]["answer"] = "650元超过700元上限，因此不能报销。"
            return decision
        result = self.run_task(policy=malicious_prose)
        self.assertEqual(result["status"], "answered")
        self.assertIn("给定金额未超过此金额上限", result["output"]["answer"])
        self.assertNotIn("不能报销", result["output"]["answer"])
        self.assertTrue(grade(self.root / "demo")["passed"])
        # A tampered result file also fails the independent display check.
        result["output"]["answer"] = "650元超过700元上限，因此不能报销。"
        core.write_json(self.root / "demo" / "result.json", result)
        self.assertFalse(grade(self.root / "demo")["passed"])

    def test_handoff_cannot_invent_conflict_or_restricted_evidence(self):
        forged = policies.finish("human_required", refs=["P21-v1#1"], answer="两份材料冲突")
        result = self.run_task("T07", policy=lambda _v: forged)
        self.assertEqual(result["status"], "invalid_output")
        self.assertEqual(result["budget"]["tool_calls_started"], 0)
        self.assertFalse(grade(self.root / "demo")["passed"])

    def test_grader_rejects_document_id_mismatch(self):
        result = self.run_task()
        result["output"]["claims"][0]["document_id"] = "invented"
        core.write_json(self.root / "demo" / "result.json", result)
        self.assertFalse(grade(self.root / "demo")["passed"])

    def test_completed_result_is_not_returned_after_tenant_or_role_changes(self):
        users = core.read_json(core.USER_FILE)
        user_file = self.root / "users.json"
        core.write_json(user_file, users)
        with patch.object(core, "USER_FILE", user_file):
            waiting = self.run_task("T11")
            core.approve_task("demo", waiting["approval_request"]["request_id"], self.root)
            self.assertEqual(core.resume_task("demo", self.root)["status"], "write_succeeded")
            users["U001"]["tenant_id"] = "demo-b"
            users["U001"]["role"] = "revoked"
            core.write_json(user_file, users)
            denied = core.resume_task("demo", self.root)
        self.assertEqual(denied["status"], "permission_denied")
        for field in ("output", "object_id", "operation_id", "approval_request"):
            self.assertIsNone(denied[field])
        context = core.read_json(self.root / "demo" / "context.json")
        self.assertEqual(context["known"], {})
        self.assertEqual(context["messages"], [])
        self.assertEqual(len(self.stores().snapshot()), 1)

    def test_search_contract_rejects_undocumented_natural_language_query(self):
        call = {"call_id": "c1", "name": "search_policy", "arguments": {"query": "住宿标准", "city": "海岚", "trip_date": "2026-11-12"}}
        result = self.run_task(policy=lambda _v: {"tool_calls": [call], "output": None})
        self.assertEqual(result["status"], "invalid_output")
        self.assertEqual(result["budget"]["tool_calls_started"], 0)

    def test_business_date_handles_boundary_and_rejects_naive_input(self):
        self.assertEqual(business_date("2026-10-31T15:59:59+00:00"), "2026-10-31")
        self.assertEqual(business_date("2026-10-31T16:00:00Z"), "2026-11-01")
        with self.assertRaises(ValueError):
            business_date("2026-11-01T00:00:00")

    def test_tool_schema_and_runtime_schema_stay_identical(self):
        self.assertEqual(core.read_json(core.DATA / "tools.json"), core.TOOLS)


if __name__ == "__main__":
    unittest.main()
