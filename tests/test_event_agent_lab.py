import importlib.util
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("event_lab", Path(__file__).resolve().parents[1] / "examples/event_agent_lab/lab.py")
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


class EventLabTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "state.db"
        self.receiver = lab.Receiver(self.path)
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(lambda: self.receiver.close())

    def test_all_fixed_scenarios_match_independent_expectations(self):
        for name in lab.SCENARIOS:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                result, _ = lab.run_scenario(name, directory)
                self.assertTrue(result["passed"], result)

    def test_crash_reopen_retains_one_task_and_budget(self):
        self.receiver.subscribe("s1")
        message = lab.event("different-id", 8, "新条款800元")
        with self.assertRaises(lab.SimulatedCrash):
            self.receiver.receive(message, crash_before_ack=True)
        self.receiver.close()
        self.receiver = lab.Receiver(self.path)
        self.receiver.receive(message)
        state = self.receiver.snapshot()
        self.assertEqual(len(state["tasks"]), 1)
        self.assertEqual(state["subscriptions"][0]["used"], 1)
        self.assertEqual(state["events"][0]["state"], "acked")
        self.assertIn("800", state["outbox"][0]["body"])

    def test_same_identifier_cannot_change_payload(self):
        self.receiver.subscribe("s1")
        self.receiver.receive(lab.event("e"))
        with self.assertRaises(ValueError):
            self.receiver.receive(lab.event("e", 3, "恶意替换"))
        self.assertEqual(self.receiver.snapshot()["objects"][0]["version"], 2)

    def test_replay_dispatches_committed_pending_before_ack(self):
        self.receiver.subscribe("s1")
        with self.assertRaises(lab.SimulatedCrash):
            self.receiver.receive(lab.event("after-receive"), crash_after_receive=True)
        self.assertEqual(len(self.receiver.snapshot()["pending"]), 1)
        self.assertEqual(self.receiver.snapshot()["tasks"], [])
        self.receiver.close()
        self.receiver = lab.Receiver(self.path)
        self.receiver.receive(lab.event("after-receive"))
        state = self.receiver.snapshot()
        self.assertEqual(len(state["tasks"]), 1)
        self.assertEqual(state["pending"], [])
        self.assertEqual(state["events"][0]["state"], "acked")
        self.receiver.receive(lab.event("after-receive"))
        self.assertEqual(len(self.receiver.snapshot()["outbox"]), 1)

    def test_replay_before_debounce_deadline_waits_for_explicit_timer_flush(self):
        self.receiver.close()
        self.receiver = lab.Receiver(self.path, debounce=5)
        self.receiver.subscribe("s1")
        with self.assertRaises(lab.SimulatedCrash):
            self.receiver.receive(lab.event("waiting"), now=0, crash_after_receive=True)
        self.receiver.close()
        self.receiver = lab.Receiver(self.path, debounce=5)
        self.receiver.receive(lab.event("waiting"), now=1)
        self.assertEqual(self.receiver.snapshot()["tasks"], [])
        self.receiver.flush(5)
        self.assertEqual(len(self.receiver.snapshot()["tasks"]), 1)

    def test_invalid_inputs_raise_value_error_before_changing_state(self):
        for value in (None, [], "event", 2, {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.receiver.receive(value)
        self.assertEqual(self.receiver.snapshot()["events"], [])

    def test_unchanged_version_update_refreshes_pending_reference(self):
        self.receiver.close()
        self.receiver = lab.Receiver(self.path, debounce=5)
        self.receiver.subscribe("s1")
        self.receiver.receive(lab.event("v2", 2, "700元"), now=0)
        self.receiver.receive(lab.event("v3", 3, "700元"), now=2)
        self.receiver.flush(5)
        self.assertEqual([t["version"] for t in self.receiver.snapshot()["tasks"]], [3])

    def test_conflicting_version_and_old_version_do_not_replace_new_state(self):
        self.receiver.subscribe("s1")
        self.receiver.receive(lab.event("first", 9, "上限900元"))
        self.assertEqual(self.receiver.receive(lab.event("conflict", 9, "上限1元")), "version_conflict")
        self.assertEqual(self.receiver.receive(lab.event("late", 8, "上限800元")), "stale")
        self.assertEqual(self.receiver.snapshot()["objects"][0]["content"], "上限900元")

    def test_conflicted_pending_is_quarantined_until_higher_version_resolves(self):
        self.receiver.close()
        self.receiver = lab.Receiver(self.path, debounce=5)
        self.receiver.subscribe("s1")
        first = lab.event("first-v2", 2, "700元")
        self.receiver.receive(first, now=0)
        self.assertEqual(self.receiver.receive(lab.event("conflict-v2", 2, "999元"), now=1), "version_conflict")
        self.receiver.flush(5)
        state = self.receiver.snapshot()
        self.assertEqual(state["objects"][0]["conflicted"], 1)
        self.assertEqual(state["pending"], [])
        self.assertEqual(state["tasks"], [])
        self.assertEqual(state["outbox"], [])
        self.assertEqual(state["subscriptions"][0]["used"], 0)
        self.receiver.close()
        self.receiver = lab.Receiver(self.path, debounce=5)
        # Neither replay nor another same-version agreement resolves quarantine.
        self.receiver.receive(first, now=6)
        self.receiver.receive(lab.event("v2-again", 2, "700元"), now=7)
        self.receiver.flush(20)
        self.assertEqual(self.receiver.snapshot()["tasks"], [])
        self.receiver.receive(lab.event("resolved-v3", 3, "700元"), now=21)
        self.receiver.flush(26)
        state = self.receiver.snapshot()
        self.assertEqual(state["objects"][0]["conflicted"], 0)
        self.assertEqual([task["version"] for task in state["tasks"]], [3])
        self.assertEqual(len(state["outbox"]), 1)
        self.assertIn("v3: 700元", state["outbox"][0]["body"])
        self.assertEqual(state["subscriptions"][0]["used"], 1)

    def test_conflict_does_not_pretend_to_revoke_already_accepted_work(self):
        self.receiver.subscribe("s1")
        self.receiver.receive(lab.event("accepted-v2", 2, "700元"))
        self.receiver.receive(lab.event("conflict-v2", 2, "999元"), now=1)
        self.receiver.flush(10)
        state = self.receiver.snapshot()
        self.assertEqual(state["objects"][0]["conflicted"], 1)
        self.assertEqual(len(state["tasks"]), 1)
        self.assertEqual(state["tasks"][0]["state"], "accepted")
        self.assertEqual(len(state["outbox"]), 1)

    def test_cancel_clears_pending_and_late_delivery_cannot_spawn_work(self):
        self.receiver.close()
        self.receiver = lab.Receiver(self.path, debounce=10)
        self.receiver.subscribe("s1")
        self.receiver.receive(lab.event("e"), now=0)
        self.receiver.cancel("s1")
        self.receiver.flush(20)
        self.receiver.receive(lab.event("late", 3, "750元"), now=21)
        self.receiver.flush(40)
        self.assertEqual(self.receiver.snapshot()["tasks"], [])

    def test_debounce_waits_for_latest_deadline_and_merges_versions(self):
        self.receiver.close()
        self.receiver = lab.Receiver(self.path, debounce=5)
        self.receiver.subscribe("s1")
        self.receiver.receive(lab.event("e1", 4, "800元"), now=10)
        self.receiver.receive(lab.event("e2", 5, "900元"), now=12)
        self.receiver.flush(16)
        self.assertEqual(self.receiver.snapshot()["tasks"], [])
        self.receiver.flush(17)
        self.assertEqual([t["version"] for t in self.receiver.snapshot()["tasks"]], [5])

    def test_trigger_permission_and_notification_are_separate(self):
        self.receiver.subscribe("denied", review_allowed=False)
        self.receiver.subscribe("silent", owner="learner-b", notify=False)
        self.receiver.receive(lab.event("first"))
        state = self.receiver.snapshot()
        self.assertEqual([t["owner"] for t in state["tasks"]], ["learner-b"])
        self.assertEqual(state["outbox"], [])
        self.receiver.receive(lab.event("same-text-new-version", 3))
        self.assertEqual(len(self.receiver.snapshot()["tasks"]), 1)

    def test_exhausted_budget_survives_reopen_and_self_event_is_ignored(self):
        self.receiver.subscribe("s1", budget=1)
        self.receiver.receive(lab.event("one", 2, "700元"))
        self.receiver.close()
        self.receiver = lab.Receiver(self.path)
        self.receiver.receive(lab.event("self", 90, "回写", origin="this-lab"))
        self.receiver.receive(lab.event("two", 3, "800元"))
        state = self.receiver.snapshot()
        self.assertEqual(len(state["tasks"]), 1)
        self.assertEqual(state["objects"][0]["version"], 3)


if __name__ == "__main__":
    unittest.main()
