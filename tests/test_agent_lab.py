"""Behavior checks for the offline teaching runtime, using only the stdlib."""

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest


LAB_PATH = Path(__file__).resolve().parents[1] / "examples" / "agent_lab" / "lab.py"
SPEC = importlib.util.spec_from_file_location("interview_agent_lab", LAB_PATH)
assert SPEC and SPEC.loader
lab = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lab
SPEC.loader.exec_module(lab)


class AgentLabTests(unittest.TestCase):
    def test_search_returns_only_matching_synthetic_documents(self):
        runtime = lab.Runtime()
        result = runtime.invoke(lab.Action("search", {"query": "retry", "top_k": 1}))
        self.assertEqual([doc["id"] for doc in result["documents"]], ["D2"])
        self.assertEqual(runtime.invoke(lab.Action("search", {"query": "zzzz_unknown"})), {"documents": []})

    def test_unknown_tool_stops_before_any_tool_execution(self):
        runtime = lab.Runtime()
        result = lab.run(lab.scripted([lab.Action("run_shell", {"command": "anything"})]), runtime)
        self.assertEqual(result.stop_reason, "unknown_tool")
        self.assertEqual((runtime.search_attempts, runtime.write_attempts, runtime.tickets), (0, 0, {}))

    def test_invalid_search_arguments_have_no_tool_side_effect(self):
        invalid_args = [None, {}, {"query": ""}, {"query": 5}, {"query": "x", "top_k": True}, {"query": "x", "top_k": 0}, {"query": "x", "top_k": 6}, {"query": "x", "admin": True}]
        for args in invalid_args:
            with self.subTest(args=args):
                runtime = lab.Runtime()
                result = lab.run(lab.scripted([lab.Action("search", args)]), runtime)
                self.assertEqual(result.stop_reason, "invalid_arguments")
                self.assertEqual(runtime.search_attempts, 0)

    def test_unapproved_write_does_not_execute(self):
        runtime = lab.Runtime()
        action = lab.Action("create_ticket", {"request_id": "one", "title": "Synthetic task"})
        result = lab.run(lab.scripted([action]), runtime)
        self.assertEqual(result.stop_reason, "approval_required")
        self.assertEqual((runtime.write_attempts, runtime.tickets), (0, {}))

    def test_model_cannot_supply_approval_in_arguments(self):
        action = lab.Action("create_ticket", {"request_id": "one", "title": "Synthetic task", "approved": True})
        runtime = lab.Runtime(approvals=frozenset({lab.Approval("one", "Synthetic task")}))
        result = lab.run(lab.scripted([action]), runtime)
        self.assertEqual(result.stop_reason, "invalid_arguments")
        self.assertEqual((runtime.write_attempts, runtime.tickets), (0, {}))

    def test_approval_is_bound_to_exact_action(self):
        runtime = lab.Runtime(approvals=frozenset({lab.Approval("one", "Approved title")}))
        for action in [lab.Action("create_ticket", {"request_id": "one", "title": "Changed title"}), lab.Action("create_ticket", {"request_id": "two", "title": "Approved title"})]:
            with self.subTest(action=action):
                self.assertEqual(lab.run(lab.scripted([action]), runtime).stop_reason, "approval_required")
        self.assertEqual((runtime.write_attempts, runtime.tickets), (0, {}))

    def test_duplicate_approved_intent_returns_same_ticket(self):
        runtime = lab.Runtime(approvals=frozenset({lab.Approval("one", "Task")}))
        action = lab.Action("create_ticket", {"request_id": "one", "title": "Task"})
        first = runtime.invoke(action)
        second = runtime.invoke(action)
        self.assertFalse(first["replayed"])
        self.assertTrue(second["replayed"])
        self.assertEqual(first["ticket"]["ticket_id"], second["ticket"]["ticket_id"])
        self.assertEqual((len(runtime.tickets), runtime.write_attempts), (1, 2))

    def test_idempotency_key_reuse_with_different_content_is_rejected(self):
        runtime = lab.Runtime(approvals=frozenset({lab.Approval("one", "A"), lab.Approval("one", "B")}))
        result = lab.run(lab.scripted([lab.Action("create_ticket", {"request_id": "one", "title": "A"}), lab.Action("create_ticket", {"request_id": "one", "title": "B"})]), runtime)
        self.assertEqual(result.stop_reason, "idempotency_conflict")
        self.assertEqual(runtime.lookup_ticket("one")["title"], "A")
        self.assertEqual(len(runtime.tickets), 1)

    def test_transient_read_recovers_within_retry_limit(self):
        runtime = lab.Runtime(transient_read_failures=1)
        result = lab.run(lab.scripted([lab.Action("search", {"query": "retry"}), lab.Finish("done")]), runtime, max_read_attempts=2)
        self.assertEqual(result.stop_reason, "final_answer")
        self.assertEqual(runtime.search_attempts, 2)
        self.assertEqual(sum(event["event"] == "observation" for event in result.events), 1)

    def test_persistent_read_failure_cannot_retry_forever(self):
        runtime = lab.Runtime(transient_read_failures=99)
        result = lab.run(lab.scripted([lab.Action("search", {"query": "retry"})]), runtime, max_read_attempts=2)
        self.assertEqual((result.stop_reason, runtime.search_attempts), ("read_retry_exhausted", 2))
        self.assertFalse(result.events[-2]["retry"])

    def test_loop_stops_at_exact_step_budget(self):
        result = lab.run(lambda _state: lab.Action("search", {"query": "agent"}), lab.Runtime(), max_steps=3)
        self.assertEqual((result.stop_reason, result.steps, result.search_attempts), ("step_budget_exhausted", 3, 3))
        for options in [{"max_steps": 0}, {"max_steps": True}, {"max_read_attempts": 0}, {"max_read_attempts": True}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                lab.run(lambda _state: lab.Finish("done"), lab.Runtime(), **options)

    def test_lost_write_response_stops_then_reconciles_without_duplicate(self):
        runtime = lab.Runtime(approvals=frozenset({lab.Approval("one", "Task")}), lose_first_write_response=True)
        action = lab.Action("create_ticket", {"request_id": "one", "title": "Task"})
        first_run = lab.run(lab.scripted([action, action]), runtime, max_read_attempts=10)
        self.assertEqual(first_run.stop_reason, "write_outcome_unknown")
        self.assertEqual(runtime.write_attempts, 1)  # The runner did not retry a write.
        stored = runtime.lookup_ticket("one")
        self.assertIsNotNone(stored)
        second_run = lab.run(lab.scripted([action, lab.Finish("reconciled")]), runtime)
        self.assertEqual(second_run.stop_reason, "final_answer")
        self.assertEqual((len(runtime.tickets), runtime.write_attempts), (1, 2))
        # A new process/runtime has no durable deduplication record.
        self.assertIsNone(lab.Runtime().lookup_ticket("one"))

    def test_all_cli_scenarios_self_check_and_emit_machine_readable_trace(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = lab.main(["--scenario", "all"])
        lines = [json.loads(line) for line in output.getvalue().splitlines()]
        summaries = [line for line in lines if "summary" in line]
        self.assertEqual(code, 0)
        self.assertEqual({line["scenario"] for line in summaries}, set(lab.SCENARIOS))
        self.assertTrue(all(line["summary"]["self_check"] == "pass" for line in summaries))


if __name__ == "__main__":
    unittest.main()
