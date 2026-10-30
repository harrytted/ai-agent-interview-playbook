"""The crash test deliberately crosses real process/transaction boundaries."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from examples.policy_agent.storage import Stores

ROOT = Path(__file__).resolve().parents[1]


class PolicyCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_root = Path(self.temp.name) / "runs"

    def cli(self, *args):
        return subprocess.run([sys.executable, "-m", "examples.policy_agent", "--root", str(self.run_root), *args], cwd=ROOT, capture_output=True, text=True)

    def test_crash_after_service_commit_resumes_in_new_process_with_one_object(self):
        initial = self.cli("run", "--task", "T12", "--run-id", "crash-demo")
        self.assertEqual(initial.returncode, 0, initial.stderr)
        waiting = json.loads(initial.stdout)
        approved = self.cli("approve", "--run-id", "crash-demo", "--request-id", waiting["approval_request"]["request_id"])
        self.assertEqual(approved.returncode, 0, approved.stderr)
        crashed = self.cli("resume", "--run-id", "crash-demo")
        self.assertEqual(crashed.returncode, 73, crashed.stderr)
        stores = Stores(self.run_root / "crash-demo")
        self.assertEqual(len(stores.snapshot()), 1)
        before = stores.snapshot()[0]
        recovered = self.cli("resume", "--run-id", "crash-demo")
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        result = json.loads(recovered.stdout)
        self.assertEqual(result["status"], "write_succeeded")
        self.assertEqual(result["object_id"], before["object_id"])
        self.assertEqual(len(stores.snapshot()), 1)
        self.assertEqual(self.cli("resume", "--run-id", "crash-demo").returncode, 0)
        self.assertEqual(len(stores.snapshot()), 1)
        events = [json.loads(line) for line in (stores.run_dir / "trace.jsonl").read_text().splitlines()]
        self.assertEqual(len([e for e in events if e["event"] == "tool_started" and e["name"] == "create_ticket"]), 1)
        self.assertTrue(any(e.get("action") == "reconcile" for e in events))

    def test_missing_reply_round_trip_and_existing_directory_refusal(self):
        first = self.cli("run", "--task", "T01", "--variant", "missing-date", "--run-id", "missing")
        self.assertEqual(json.loads(first.stdout)["status"], "clarification_required")
        repeated = self.cli("run", "--task", "T01", "--run-id", "missing")
        self.assertEqual(repeated.returncode, 2)
        resumed = self.cli("resume", "--run-id", "missing", "--reply-json", '{"trip_date":"2026-11-12"}')
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        result = json.loads(resumed.stdout)
        self.assertEqual((result["status"], result["budget"]["decisions_used"]), ("answered", 3))

    def test_pilot_eval_exit_code_and_machine_readable_report(self):
        output = self.run_root / "report.json"
        result = self.cli("eval", "--suite", "pilot", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(output.read_text())
        self.assertEqual((report["total"], report["passed"]), (3, 3))

    def test_invalid_run_path_and_unknown_task_are_configuration_errors(self):
        for args in [("run", "--task", "unknown"), ("run", "--task", "T01", "--run-id", "../escape")]:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error", json.loads(result.stderr))


if __name__ == "__main__":
    unittest.main()
