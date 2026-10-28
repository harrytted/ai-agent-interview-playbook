from contextlib import closing, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest


PATH = Path(__file__).resolve().parents[1] / "examples/advanced/runtime_lab.py"
SPEC = importlib.util.spec_from_file_location("advanced_runtime_lab", PATH)
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)


class AdvancedRuntimeTests(unittest.TestCase):
    def test_pass_at_k_counts_subsets_and_extreme_outcomes(self):
        self.assertAlmostEqual(lab.pass_at_k(5, 1, 2), 0.4)
        self.assertEqual(lab.pass_at_k(5, 0, 2), 0)
        self.assertEqual(lab.pass_at_k(5, 5, 2), 1)
        self.assertEqual(lab.pass_at_k(5, 1, 5), 1)
        self.assertAlmostEqual(lab.pass_at_k(5, 2, 1), 2 / 5)

    def test_invalid_pass_at_k_inputs_are_rejected(self):
        for args in [(0, 0, 1), (5, 6, 1), (5, -1, 1), (5, 1, 6), (5, 1, 0), (True, 1, 1)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                lab.pass_at_k(*args)

    def test_repeated_success_is_averaged_per_task(self):
        metrics = lab.iid_reliability([0.9, 0.1], 2)
        self.assertAlmostEqual(metrics["mean_at_least_one"], 0.59)
        self.assertAlmostEqual(metrics["mean_all_succeed"], 0.41)
        self.assertNotAlmostEqual(metrics["mean_at_least_one"], 0.75)
        for probabilities, k in [([], 2), ([float("nan")], 2), ([1.1], 2), ([True], 2), ([0.5], 0)]:
            with self.assertRaises(ValueError):
                lab.iid_reliability(probabilities, k)

    def test_group_rewards_are_centered_and_equal_rewards_have_no_signal(self):
        self.assertEqual(lab.relative_advantages([0, 0, 1, 1]), [-1, -1, 1, 1])
        self.assertEqual(lab.relative_advantages([4, 4]), [0, 0])
        with self.assertRaises(ValueError):
            lab.relative_advantages([])

    def test_denied_reservation_leaves_shared_budget_unchanged(self):
        budget = lab.Budget(1000, 2)
        budget.reserve("a", 600)
        with self.assertRaises(lab.BudgetExceeded):
            budget.reserve("b", 500)
        self.assertEqual((budget.used, budget.reservations), (600, {"a": 600}))
        budget.reserve("b", 400)
        self.assertEqual(budget.used, 1000)

    def test_group_reward_signal_survives_extreme_scales(self):
        for rewards in ([1e-200, 2e-200], [1e308, 1.5e308]):
            with self.subTest(rewards=rewards):
                result = lab.relative_advantages(rewards)
                self.assertAlmostEqual(result[0], -1)
                self.assertAlmostEqual(result[1], 1)

    def test_reservation_replay_and_call_count_limit(self):
        budget = lab.Budget(100, 1)
        budget.reserve("a", 10)
        budget.reserve("a", 10)
        self.assertEqual(budget.used, 10)
        with self.assertRaises(ValueError):
            budget.reserve("a", 20)
        with self.assertRaises(lab.BudgetExceeded):
            budget.reserve("b", 1)
        with self.assertRaises(ValueError):
            budget.reserve("c", True)

    def test_dag_critical_path_obeys_dependencies(self):
        result = lab.critical_path({"p": (200, []), "a": (300, ["p"]), "b": (500, ["p"]), "s": (400, ["a", "b"])})
        self.assertEqual(result["serial_ms"], 1400)
        self.assertEqual(result["parallel_lower_bound_ms"], 1100)
        self.assertEqual(result["finish_ms"]["s"], 1100)
        self.assertEqual(lab.critical_path({})["parallel_lower_bound_ms"], 0)

    def test_invalid_dependency_graphs_fail_before_prediction(self):
        for graph in [{"a": (1, ["a"])}, {"a": (1, ["b"])}, {"a": (-1, [])}]:
            with self.assertRaises(ValueError):
                lab.critical_path(graph)

    def test_remote_commit_survives_missing_local_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            local, remote = Path(directory) / "local.db", Path(directory) / "remote.db"
            with self.assertRaises(lab.SimulatedCrash):
                lab.run_operation(local, remote, "one", "A", crash_after_remote=True)
            with closing(sqlite3.connect(local)) as conn:
                self.assertEqual(conn.execute("SELECT status FROM intents").fetchone()[0], "pending")
            with closing(sqlite3.connect(remote)) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0], 1)
            ticket_id = lab.run_operation(local, remote, "one", "A")
            self.assertEqual(lab.run_operation(local, remote, "one", "A"), ticket_id)
            with closing(sqlite3.connect(remote)) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0], 1)

    def test_reused_operation_id_cannot_silently_change_content(self):
        with tempfile.TemporaryDirectory() as directory:
            local, remote = Path(directory) / "local.db", Path(directory) / "remote.db"
            lab.run_operation(local, remote, "one", "A")
            with self.assertRaises(ValueError):
                lab.run_operation(local, remote, "one", "B")
            with self.assertRaises(ValueError):
                lab.remote_apply(remote, "one", "B")
            self.assertNotEqual(lab.run_operation(local, remote, "two", "A"), lab.run_operation(local, remote, "one", "A"))

    def test_replay_demo_finishes_one_object(self):
        result = lab.replay_demo()
        self.assertEqual((result["status_after_crash"], result["status_after_resume"]), ("pending", "done"))
        self.assertEqual(result["ticket_after_resume"], result["ticket_after_replay"])
        self.assertEqual(result["remote_object_count"], 1)

    def test_all_cli_scenarios_emit_valid_json(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(lab.main(["--scenario", "all"]), 0)
        rows = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([x["scenario"] for x in rows], ["evaluation", "budget", "replay"])


if __name__ == "__main__":
    unittest.main()
