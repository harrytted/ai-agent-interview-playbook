"""Execute SQL on a tenant-scoped SQLite snapshot, then grade independently.

Default SQL candidates are prepared fixtures. No natural-language model is called.
SQLite has no PostgreSQL-style users/RLS here: the trusted host copies permitted
rows into a private connection before exposing the candidate execution surface.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sqlite3
import time


HERE = Path(__file__).resolve().parent
SCENARIOS = ("normal", "join-amplification", "schema-repair", "bounded-repair", "semantic-error", "access-control", "resource-limit", "clarification")
PARAMETERS = {"start": "2026-10-01", "end": "2026-11-01"}
TRUSTED_USERS = {"alice": "tenant-a", "bob": "tenant-b"}
ALLOWED = {
    "employees": {"id", "name", "department"},
    "applications": {"id", "employee_id", "submitted_at", "approved_at", "amount_cents", "limit_cents", "status", "city"},
    "expenses": {"id", "application_id", "category", "amount_cents"},
}
FUNCTIONS = {"sum", "count", "coalesce", "round", "abs", "min", "max", "nullif", "avg", "date", "substr", "lower", "upper"}
CORRECT_SQL = """SELECT COALESCE(SUM(amount_cents), 0) AS total_cents,
COUNT(*) AS application_count,
COALESCE(SUM(CASE WHEN amount_cents IS NOT NULL AND limit_cents IS NOT NULL THEN 1 ELSE 0 END), 0) AS comparable_count,
COALESCE(SUM(CASE WHEN amount_cents > limit_cents THEN 1 ELSE 0 END), 0) AS over_count,
ROUND(1.0 * SUM(CASE WHEN amount_cents > limit_cents THEN 1 ELSE 0 END) /
NULLIF(SUM(CASE WHEN amount_cents IS NOT NULL AND limit_cents IS NOT NULL THEN 1 ELSE 0 END), 0), 6) AS over_rate
FROM applications
WHERE submitted_at >= :start AND submitted_at < :end
AND status IN ('submitted', 'approved')"""
BROKEN_JOIN = """SELECT SUM(a.amount_cents) AS total_cents
FROM applications a JOIN expenses e ON a.id=e.application_id
WHERE a.submitted_at >= :start AND a.submitted_at < :end
AND a.status IN ('submitted', 'approved')"""
DISTINCT_JOIN = BROKEN_JOIN.replace("SUM(a.amount_cents)", "SUM(DISTINCT a.amount_cents)")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def metric_card(specification):
    """The host requires explicit business choices; it does not infer them."""
    required = ("start", "end", "date_basis", "amount_unit", "statuses", "over_denominator")
    missing = [key for key in required if specification.get(key) in (None, "", [])]
    if missing:
        return {"status": "needs_clarification", "missing": missing}
    if specification["date_basis"] != "submitted_at" or specification["amount_unit"] != "cents" or specification["over_denominator"] != "known_amount_and_limit" or specification["statuses"] != ["submitted", "approved"]:
        return {"status": "unsupported_metric", "reason": "this lab supports one explicitly declared metric contract"}
    from datetime import date
    for key in ("start", "end"):
        value = specification[key]
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError("metric dates must use YYYY-MM-DD")
    if specification["start"] >= specification["end"]:
        raise ValueError("invalid metric interval")
    return {"status": "ready", **specification, "grain": "one row per application", "null_amount_total": "SUM ignores NULL; report comparable_count separately", "schema_links": {"申请金额": "applications.amount_cents", "申请日期": "applications.submitted_at", "审批日期": "applications.approved_at", "明细归属": "expenses.application_id -> applications.id"}}


def complete_card():
    return metric_card({**PARAMETERS, "date_basis": "submitted_at", "amount_unit": "cents", "statuses": ["submitted", "approved"], "over_denominator": "known_amount_and_limit"})


def create_source(path, variant="base"):
    data = read_json(HERE / "data" / "datasets.json")[variant]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()  # this function owns this disposable fixture path only
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE employees(id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT, department TEXT, salary_cents INTEGER);
        CREATE TABLE applications(id TEXT PRIMARY KEY, employee_id TEXT REFERENCES employees(id), submitted_at TEXT, approved_at TEXT, amount_cents INTEGER, limit_cents INTEGER, status TEXT, city TEXT);
        CREATE TABLE expenses(id TEXT PRIMARY KEY, application_id TEXT REFERENCES applications(id), category TEXT, amount_cents INTEGER);
        """)
        db.executemany("INSERT INTO employees VALUES(?,?,?,?,?)", data["employees"])
        db.executemany("INSERT INTO applications VALUES(?,?,?,?,?,?,?,?)", data["applications"])
        db.executemany("INSERT INTO expenses VALUES(?,?,?,?)", data["expenses"])
    return path


@dataclass(frozen=True)
class Limits:
    max_steps: int = 20000
    max_rows: int = 100
    max_sql_bytes: int = 16000
    timeout_seconds: float = 1.0


class SQLSandbox:
    """Scoped data + SQLite authorizer + bounded query execution.

    This is an application boundary inside a trusted process, not an OS sandbox.
    The SQL candidate cannot choose a tenant, source path, connection or ACL.
    """

    def __init__(self, source, user="alice"):
        if user not in TRUSTED_USERS:
            raise PermissionError("unknown trusted test identity")
        self.user = user
        self.tenant = TRUSTED_USERS[user]
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
        CREATE TABLE employees(id TEXT PRIMARY KEY, name TEXT, department TEXT, tenant_id TEXT);
        CREATE TABLE applications(id TEXT PRIMARY KEY, employee_id TEXT, submitted_at TEXT, approved_at TEXT, amount_cents INTEGER, limit_cents INTEGER, status TEXT, city TEXT);
        CREATE TABLE expenses(id TEXT PRIMARY KEY, application_id TEXT, category TEXT, amount_cents INTEGER);
        """)
        # Only these host-authored, parameterized statements see the source DB.
        uri = Path(source).resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as origin:
            employees = origin.execute("SELECT id,name,department,tenant_id FROM employees WHERE tenant_id=?", (self.tenant,)).fetchall()
            applications = origin.execute("SELECT a.* FROM applications a JOIN employees u ON a.employee_id=u.id WHERE u.tenant_id=?", (self.tenant,)).fetchall()
            expenses = origin.execute("SELECT e.* FROM expenses e JOIN applications a ON e.application_id=a.id JOIN employees u ON a.employee_id=u.id WHERE u.tenant_id=?", (self.tenant,)).fetchall()
        self.db.executemany("INSERT INTO employees VALUES(?,?,?,?)", employees)
        self.db.executemany("INSERT INTO applications VALUES(?,?,?,?,?,?,?,?)", applications)
        self.db.executemany("INSERT INTO expenses VALUES(?,?,?,?)", expenses)
        self.db.commit()
        self.db.execute("PRAGMA query_only=ON")
        if hasattr(self.db, "setlimit"):
            self.db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 131072)
            self.db.setlimit(sqlite3.SQLITE_LIMIT_COLUMN, 32)
            self.db.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 50)
        self.denial = None
        self.db.set_authorizer(self._authorize)

    def _authorize(self, action, first, second, database, trigger):
        if action == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_READ:
            if (database == "main" or (database is None and second == "")) and first in ALLOWED and (second in ALLOWED[first] or second == ""):
                return sqlite3.SQLITE_OK
            self.denial = f"read denied: {database}.{first}.{second}"
        elif action == sqlite3.SQLITE_FUNCTION:
            if (second or "").lower() in FUNCTIONS:
                return sqlite3.SQLITE_OK
            self.denial = "function denied: " + str(second)
        elif action == getattr(sqlite3, "SQLITE_RECURSIVE", -1):
            return sqlite3.SQLITE_OK  # permitted computation still has a step budget
        else:
            self.denial = "statement operation denied: " + str(action)
        return sqlite3.SQLITE_DENY

    def execute(self, sql, parameters=None, limits=Limits()):
        if not isinstance(sql, str) or len(sql.encode("utf-8")) > limits.max_sql_bytes:
            return {"status": "rejected", "reason": "SQL text limit"}
        if not re.match(r"^\s*(SELECT|WITH)\b", sql, re.IGNORECASE):
            return {"status": "rejected", "reason": "only SELECT or WITH candidates are accepted"}
        if limits.max_steps < 1 or limits.max_rows < 1 or limits.timeout_seconds <= 0:
            raise ValueError("limits must be positive")
        self.denial = None
        steps = 0
        deadline = time.monotonic() + limits.timeout_seconds

        def progress():
            nonlocal steps
            steps += 100
            return int(steps >= limits.max_steps or time.monotonic() >= deadline)

        self.db.set_progress_handler(progress, 100)
        cursor = None
        try:
            cursor = self.db.execute(sql, parameters or {})  # one statement only
            rows = cursor.fetchmany(limits.max_rows + 1)
            if len(rows) > limits.max_rows:
                return {"status": "resource_limit", "reason": "result row limit", "steps_approximately": steps}
            return {"status": "ok", "columns": [column[0] for column in cursor.description], "rows": [list(row) for row in rows], "steps_approximately": steps, "scope": {"user": self.user, "tenant": self.tenant}}
        except sqlite3.Error as error:
            message = str(error)
            status = "rejected" if self.denial else "resource_limit" if "interrupted" in message else "invalid_sql"
            return {"status": status, "reason": self.denial or message, "steps_approximately": steps}
        finally:
            if cursor:
                cursor.close()
            self.db.set_progress_handler(None, 0)

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def execute_candidates(sandbox, candidates, max_attempts=2):
    """Prepared candidates consume only execution feedback, never expected data."""
    attempts = []
    for sql in candidates[:max_attempts]:
        result = sandbox.execute(sql, PARAMETERS)
        attempts.append({"attempt": len(attempts) + 1, "sql": sql, "feedback": result})
        if result["status"] == "ok":
            return {"status": "candidate_executed", "attempts": attempts, "result": result}
        if result["status"] in ("rejected", "resource_limit"):
            break
    return {"status": "stopped", "reason": "no executable candidate within attempt/access/resource limits", "attempts": attempts}


def compare_metric(result, expected):
    if result.get("status") != "ok" or len(result.get("rows", [])) != 1:
        return False
    actual = dict(zip(result["columns"], result["rows"][0]))
    for field, wanted in expected.items():
        got = actual.get(field)
        if isinstance(wanted, float):
            if not isinstance(got, (int, float)) or abs(got - wanted) > 0.000001:
                return False
        elif got != wanted:
            return False
    return True


def conclusion_evidence(result):
    """A deterministic candidate report; the independent grade decides validity."""
    if result.get("status") != "ok" or len(result.get("rows", [])) != 1:
        return {"status": "unavailable", "reason": "no single successful result row"}
    row = dict(zip(result["columns"], result["rows"][0]))
    required = ("total_cents", "application_count", "comparable_count", "over_count", "over_rate")
    if any(field not in row for field in required):
        return {"status": "unavailable", "reason": "candidate did not return the metric columns"}
    amount = row["total_cents"]
    rate = row["over_rate"]
    if not isinstance(amount, (int, float)) or not (rate is None or isinstance(rate, (int, float))):
        return {"status": "unavailable", "reason": "candidate metric types are not numeric"}
    rate_text = "无法计算" if rate is None else f"{rate * 100:g}%"
    return {"status": "candidate_report; requires independent grade", "text": f"候选查询报告：当前可见范围内，已知申请金额 {amount / 100:g} 元；申请 {row['application_count']} 笔，可比较 {row['comparable_count']} 笔，超标 {row['over_count']} 笔，占可比较申请的 {rate_text}。", "evidence": {field: {"result_row": 0, "column": field, "value": row[field]} for field in required}}


def exercise(scenario, output, candidate=None):
    output = Path(output)
    observation = {"metric_card": complete_card(), "candidate_source": "prepared-offline-fixture", "model_calls": 0}
    events = []
    variants = ("base", "duplicate-amounts", "missing-values") if scenario in ("normal", "join-amplification", "candidate") else ("base",)
    for variant in variants:
        source = create_source(output / (variant + ".sqlite"), variant)
        with SQLSandbox(source) as sandbox:
            if scenario in ("normal", "candidate"):
                sql = CORRECT_SQL if candidate is None else candidate["sql"]
                result = sandbox.execute(sql, PARAMETERS)
                observation[variant] = {"sql": sql, "result": result, "conclusion": conclusion_evidence(result)}
                if candidate:
                    observation["candidate_source"] = "external-sql-file; model provenance not verified"
            elif scenario == "join-amplification":
                observation[variant] = {"broken": sandbox.execute(BROKEN_JOIN, PARAMETERS), "distinct": sandbox.execute(DISTINCT_JOIN, PARAMETERS), "corrected": sandbox.execute(CORRECT_SQL, PARAMETERS)}
            elif scenario == "schema-repair":
                observation["run"] = execute_candidates(sandbox, [CORRECT_SQL.replace("SUM(amount_cents)", "SUM(invented_amount)"), CORRECT_SQL])
            elif scenario == "bounded-repair":
                bad = "SELECT invented_column FROM applications"
                observation["run"] = execute_candidates(sandbox, [bad] * 5, max_attempts=2)
            elif scenario == "semantic-error":
                observation["result"] = sandbox.execute(CORRECT_SQL.replace("WHERE submitted_at", "WHERE approved_at").replace("AND submitted_at <", "AND approved_at <"), PARAMETERS)
            elif scenario == "access-control":
                candidates = {"write": "DELETE FROM applications", "with_write": "WITH ids AS (SELECT id FROM applications) DELETE FROM applications WHERE id IN (SELECT id FROM ids)", "attach": "ATTACH DATABASE ':memory:' AS outside", "private_column": "SELECT tenant_id FROM employees", "salary_not_copied": "SELECT salary_cents FROM employees", "catalog": "SELECT sql FROM sqlite_master", "pragma": "PRAGMA database_list", "extension": "SELECT load_extension('anything')", "multi_statement": "SELECT 1; DELETE FROM applications"}
                observation["denials"] = {name: sandbox.execute(sql) for name, sql in candidates.items()}
                observation["scoped_rows"] = sandbox.execute("SELECT id FROM applications WHERE 1=1 OR employee_id='e3'")
                observation["after"] = sandbox.execute(CORRECT_SQL, PARAMETERS)
            elif scenario == "resource-limit":
                observation["steps"] = sandbox.execute("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<10000000) SELECT SUM(x) FROM n", limits=Limits(max_steps=1000))
                observation["rows"] = sandbox.execute("SELECT id FROM applications", limits=Limits(max_rows=1))
                observation["text"] = sandbox.execute("SELECT '" + "x" * 200 + "'", limits=Limits(max_sql_bytes=100))
                observation["after"] = sandbox.execute(CORRECT_SQL, PARAMETERS)
            elif scenario == "clarification":
                observation["ambiguous"] = metric_card({"start": PARAMETERS["start"], "end": PARAMETERS["end"]})
                observation["executed_before_clarification"] = False
                observation["result_after_clarification"] = sandbox.execute(CORRECT_SQL, PARAMETERS)
        events.append({"event": "scenario_execution", "scenario": scenario, "dataset": variant, "observation": observation.get(variant, observation)})
    return observation, events


def grade(scenario, observation):
    expected = read_json(HERE / "data" / "expected.json")
    checks = {}
    if scenario in ("normal", "candidate"):
        checks = {variant: compare_metric(observation[variant]["result"], expected[variant]) for variant in expected}
    elif scenario == "join-amplification":
        for variant, facts in expected.items():
            value = observation[variant]
            checks[variant + "_correct"] = compare_metric(value["corrected"], facts)
        checks["hand_calculable_counterexample"] = observation["base"]["broken"]["rows"] == [[200000]] and expected["base"]["total_cents"] == 135000
        checks["distinct_is_not_general_repair"] = observation["duplicate-amounts"]["distinct"]["rows"] == [[65000]] and expected["duplicate-amounts"]["total_cents"] == 130000
    elif scenario == "schema-repair":
        run = observation["run"]
        checks = {"first_invalid": run["attempts"][0]["feedback"]["status"] == "invalid_sql", "two_attempts": len(run["attempts"]) == 2, "semantic_result": compare_metric(run["result"], expected["base"])}
    elif scenario == "bounded-repair":
        checks = {"bounded": len(observation["run"]["attempts"]) == 2, "stopped": observation["run"]["status"] == "stopped"}
    elif scenario == "semantic-error":
        checks = {"SQL_did_execute": observation["result"]["status"] == "ok", "independent_grader_detected_wrong_date": not compare_metric(observation["result"], expected["base"])}
    elif scenario == "access-control":
        checks = {name: result["status"] != "ok" for name, result in observation["denials"].items()}
        checks["tenant_rows_only"] = sorted(row[0] for row in observation["scoped_rows"]["rows"]) == ["a1", "a2", "a3"]
        checks["unchanged_metric"] = compare_metric(observation["after"], expected["base"])
    elif scenario == "resource-limit":
        checks = {"steps_bounded": observation["steps"]["status"] == "resource_limit", "rows_bounded": observation["rows"]["status"] == "resource_limit", "SQL_text_bounded": observation["text"]["status"] == "rejected", "connection_recovers": compare_metric(observation["after"], expected["base"])}
    elif scenario == "clarification":
        checks = {"missing_choices_reported": observation["ambiguous"]["status"] == "needs_clarification" and "date_basis" in observation["ambiguous"]["missing"], "no_premature_query": not observation["executed_before_clarification"], "correct_after_clarification": compare_metric(observation["result_after_clarification"], expected["base"])}
    return {"scenario": scenario, "passed": bool(checks) and all(checks.values()), "checks": checks, "evidence_level": "real-sqlite-execution; no-NL-model-evaluation"}


def run_scenario(scenario, output, candidate=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    observation, events = exercise(scenario, output, candidate)
    evaluation = grade(scenario, observation)
    write_json(output / "result.json", observation)
    write_json(output / "grade.json", evaluation)
    (output / "trace.jsonl").write_text("".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events), encoding="utf-8")
    return evaluation


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all", "candidate") + SCENARIOS, default="all")
    parser.add_argument("--output", type=Path, default=Path(".local/sql_agent_lab"))
    parser.add_argument("--candidate-file", type=Path, help="JSON with sql and optional provenance; executed on the fixed three-dataset metric contract")
    args = parser.parse_args(argv)
    if args.scenario == "candidate" and args.candidate_file is None:
        parser.error("candidate requires --candidate-file")
    if args.candidate_file and args.scenario != "candidate":
        parser.error("--candidate-file is only used by --scenario candidate")
    candidate = read_json(args.candidate_file) if args.candidate_file else None
    if candidate is not None and (not isinstance(candidate, dict) or not isinstance(candidate.get("sql"), str)):
        parser.error("candidate file must contain a SQL string")
    selected = SCENARIOS if args.scenario == "all" else (args.scenario,)
    reports = [run_scenario(name, args.output / name, candidate) for name in selected]
    summary = {"passed": all(report["passed"] for report in reports), "scenarios": reports, "model_calls": 0, "sqlite_version": sqlite3.sqlite_version}
    write_json(args.output / "result.json", summary)
    write_json(args.output / "grade.json", {"passed": summary["passed"], "scenarios": len(reports)})
    (args.output / "trace.jsonl").write_text("".join(json.dumps({"scenario": r["scenario"], "passed": r["passed"]}) + "\n" for r in reports), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
