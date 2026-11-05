from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from examples.sql_agent_lab.lab import (
    BROKEN_JOIN, CORRECT_SQL, DISTINCT_JOIN, Limits, PARAMETERS, SCENARIOS,
    SQLSandbox, conclusion_evidence, create_source, execute_candidates, metric_card, run_scenario,
)


class SQLAgentLabTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = create_source(self.root / "source.sqlite")

    def test_join_counterexample_and_equal_amounts_defeat_distinct(self):
        with SQLSandbox(self.source) as db:
            self.assertEqual(db.execute(BROKEN_JOIN, PARAMETERS)["rows"], [[200000]])
            self.assertEqual(db.execute(CORRECT_SQL, PARAMETERS)["rows"], [[135000, 2, 2, 1, 0.5]])
        duplicate = create_source(self.root / "duplicate.sqlite", "duplicate-amounts")
        with SQLSandbox(duplicate) as db:
            self.assertEqual(db.execute(DISTINCT_JOIN, PARAMETERS)["rows"], [[65000]])
            self.assertEqual(db.execute(CORRECT_SQL, PARAMETERS)["rows"], [[130000, 2, 2, 1, 0.5]])

    def test_nulls_dates_and_cancellation_change_denominator(self):
        source = create_source(self.root / "nullable.sqlite", "missing-values")
        with SQLSandbox(source) as db:
            self.assertEqual(db.execute(CORRECT_SQL, PARAMETERS)["rows"], [[75000, 3, 1, 1, 1.0]])

    def test_tenant_scope_is_physical_even_when_candidate_removes_filter(self):
        with SQLSandbox(self.source, "alice") as db:
            result = db.execute("SELECT id FROM applications WHERE 1=1")
            self.assertEqual(sorted(row[0] for row in result["rows"]), ["a1", "a2", "a3"])
        with SQLSandbox(self.source, "bob") as db:
            self.assertEqual(db.execute("SELECT id FROM applications")["rows"], [["b1"]])
        with self.assertRaises(PermissionError):
            SQLSandbox(self.source, "invented-user")

    def test_columns_catalog_functions_and_attached_databases_are_blocked(self):
        with SQLSandbox(self.source) as db:
            for sql in ("SELECT tenant_id FROM employees", "SELECT sql FROM sqlite_master", "SELECT load_extension('x')", "SELECT * FROM pragma_database_list"):
                with self.subTest(sql=sql):
                    self.assertEqual(db.execute(sql)["status"], "rejected")
            self.assertEqual(db.execute("SELECT salary_cents FROM employees")["status"], "invalid_sql")
            self.assertEqual(db.execute("ATTACH DATABASE ':memory:' AS other")["status"], "rejected")

    def test_with_dml_does_not_bypass_select_prefix(self):
        with SQLSandbox(self.source) as db:
            result = db.execute("WITH ids AS (SELECT id FROM applications) DELETE FROM applications WHERE id IN (SELECT id FROM ids)")
            self.assertEqual(result["status"], "rejected")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM applications")["rows"], [[3]])

    def test_multiple_statements_rejected_and_original_source_is_unchanged(self):
        before = self.source.read_bytes()
        with SQLSandbox(self.source) as db:
            self.assertNotEqual(db.execute("SELECT 1; DELETE FROM applications")["status"], "ok")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM applications")["rows"], [[3]])
        self.assertEqual(self.source.read_bytes(), before)

    def test_multiple_statement_errors_across_python_versions_leave_connection_usable(self):
        message = "You can only execute one statement at a time."
        before = self.source.read_bytes()
        with SQLSandbox(self.source) as sandbox:
            connection = sandbox.db
            for error_type in (sqlite3.Warning, sqlite3.ProgrammingError):
                with self.subTest(error_type=error_type.__name__):
                    with patch.object(sandbox, "db", wraps=connection) as database:
                        database.execute.side_effect = error_type(message)
                        result = sandbox.execute("SELECT 1; DELETE FROM applications")
                        self.assertEqual(result["status"], "invalid_sql")
                        self.assertEqual(result["reason"], message)
                        database.set_progress_handler.assert_called_with(None, 0)
                    self.assertEqual(sandbox.execute("SELECT COUNT(*) FROM applications")["rows"], [[3]])
        self.assertEqual(self.source.read_bytes(), before)

    def test_step_row_and_text_limits_leave_connection_usable(self):
        with SQLSandbox(self.source) as db:
            result = db.execute("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT SUM(x) FROM n", limits=Limits(max_steps=500))
            self.assertEqual(result["status"], "resource_limit")
            self.assertEqual(db.execute("SELECT id FROM applications", limits=Limits(max_rows=1))["status"], "resource_limit")
            self.assertEqual(db.execute("SELECT '" + "x" * 101 + "'", limits=Limits(max_sql_bytes=100))["status"], "rejected")
            self.assertEqual(db.execute(CORRECT_SQL, PARAMETERS)["rows"][0][0], 135000)

    def test_repair_feedback_and_attempt_limit(self):
        with SQLSandbox(self.source) as db:
            repaired = execute_candidates(db, ["SELECT unknown_col FROM applications", CORRECT_SQL])
            self.assertEqual(len(repaired["attempts"]), 2)
            stopped = execute_candidates(db, ["SELECT unknown_col FROM applications"] * 5, 2)
            self.assertEqual(stopped["status"], "stopped")
            self.assertEqual(len(stopped["attempts"]), 2)
            denied = execute_candidates(db, ["DELETE FROM applications", CORRECT_SQL])
            self.assertEqual(len(denied["attempts"]), 1)

    def test_ambiguous_metric_cannot_silently_choose_date_or_denominator(self):
        card = metric_card({"start": "2026-10-01", "end": "2026-11-01"})
        self.assertEqual(card["status"], "needs_clarification")
        self.assertIn("date_basis", card["missing"])
        self.assertIn("over_denominator", card["missing"])

    def test_metric_dates_require_the_same_canonical_format_as_database_rows(self):
        specification = {**PARAMETERS, "date_basis": "submitted_at", "amount_unit": "cents",
                         "statuses": ["submitted", "approved"], "over_denominator": "known_amount_and_limit"}
        for start, end in (("20261001", "20261101"), ("2026-W40-4", "2026-11-01"),
                           ("2026-10-01", "20261101"), (True, "2026-11-01")):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                metric_card({**specification, "start": start, "end": end})
        self.assertEqual(metric_card(specification)["status"], "ready")

    def test_equivalent_query_is_accepted_but_wrong_date_fails(self):
        # Aliases and an equivalent predicate order should not require exact SQL.
        equivalent = {"sql": CORRECT_SQL.replace("FROM applications", "FROM applications AS a").replace("status IN ('submitted', 'approved')", "status IN ('approved', 'submitted')")}
        self.assertTrue(run_scenario("candidate", self.root / "equivalent", equivalent)["passed"])
        incorrect = {"sql": CORRECT_SQL.replace("submitted_at", "approved_at")}
        self.assertFalse(run_scenario("candidate", self.root / "incorrect", incorrect)["passed"])

    def test_conclusion_values_point_back_to_actual_result_columns(self):
        with SQLSandbox(self.source) as db:
            report = conclusion_evidence(db.execute(CORRECT_SQL, PARAMETERS))
        self.assertIn("1350 元", report["text"])
        self.assertIn("50%", report["text"])
        self.assertEqual(report["evidence"]["total_cents"]["value"], 135000)
        self.assertEqual(report["evidence"]["over_rate"]["column"], "over_rate")

    def test_unknown_and_absent_amounts_are_distinct_from_known_zero(self):
        for case, mutation, expected in (
            ("all-unknown", "UPDATE applications SET amount_cents=NULL", [None, 2, 0, 0, None]),
            ("empty", "DELETE FROM applications", [None, 0, 0, 0, None]),
            ("known-zero", "UPDATE applications SET amount_cents=0", [0, 2, 2, 0, 0.0]),
        ):
            with self.subTest(case=case):
                source = create_source(self.root / (case + ".sqlite"))
                with sqlite3.connect(source) as db:
                    db.execute(mutation)
                with SQLSandbox(source) as sandbox:
                    result = sandbox.execute(CORRECT_SQL, PARAMETERS)
                self.assertEqual(result["rows"], [expected])
                report = conclusion_evidence(result)
                self.assertEqual(report["evidence"]["total_cents"]["value"], expected[0])
                if expected[0] is None:
                    self.assertIn("无已知金额", report["text"])
                    self.assertNotIn("金额 0 元", report["text"])
                else:
                    self.assertIn("金额 0 元", report["text"])

    def test_all_scenarios_write_real_databases_and_evidence(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                destination = self.root / scenario
                self.assertTrue(run_scenario(scenario, destination)["passed"])
                self.assertTrue((destination / "base.sqlite").exists())
                self.assertTrue((destination / "trace.jsonl").read_text())


if __name__ == "__main__":
    unittest.main()
