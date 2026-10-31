#!/usr/bin/env python3
"""A local, transactional event receiver; no model, broker or external delivery."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile


class SimulatedCrash(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


class Receiver:
    """One serialized SQLite writer, explicit logical seconds, persistent budgets."""

    def __init__(self, path, *, debounce=0):
        if type(debounce) is not int or debounce < 0:
            raise ValueError("debounce must be a nonnegative integer")
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.debounce = debounce
        self.trace = []
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY, owner TEXT, object_id TEXT, active INTEGER,
            review_allowed INTEGER, notify INTEGER, budget INTEGER, used INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY, digest TEXT, state TEXT, decision TEXT, deliveries INTEGER);
        CREATE TABLE IF NOT EXISTS objects (
            id TEXT PRIMARY KEY, version INTEGER, content TEXT, conflicted INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS pending (
            subscription TEXT PRIMARY KEY, object_id TEXT, version INTEGER, content TEXT, ready_at INTEGER);
        CREATE TABLE IF NOT EXISTS tasks (
            intent_id TEXT PRIMARY KEY, run_id TEXT UNIQUE, owner TEXT, object_id TEXT,
            version INTEGER, content TEXT, state TEXT);
        CREATE TABLE IF NOT EXISTS outbox (
            intent_id TEXT PRIMARY KEY, owner TEXT, body TEXT, state TEXT);
        """)
        if "conflicted" not in {row["name"] for row in self.db.execute("PRAGMA table_info(objects)")}:
            self.db.execute("ALTER TABLE objects ADD COLUMN conflicted INTEGER NOT NULL DEFAULT 0")
        self.db.commit()

    def close(self):
        self.db.close()

    def record(self, action, **fields):
        self.trace.append({"action": action, **fields})

    def subscribe(self, subscription, owner="learner-a", object_id="policy-hailan", *,
                  review_allowed=True, notify=True, budget=2):
        if type(budget) is not int or budget < 0:
            raise ValueError("budget must be a nonnegative integer")
        # Configuration comes from the trusted host, never from event content.
        with self.db:
            self.db.execute("INSERT INTO subscriptions VALUES (?,?,?,?,?,?,?,0)",
                            (subscription, owner, object_id, 1, int(review_allowed), int(notify), budget))

    def cancel(self, subscription):
        with self.db:
            self.db.execute("UPDATE subscriptions SET active=0 WHERE id=?", (subscription,))
            self.db.execute("DELETE FROM pending WHERE subscription=?", (subscription,))
        self.record("subscription_cancelled", subscription=subscription)

    def receive(self, event, *, now=0, crash_before_ack=False, crash_after_receive=False):
        """Commit objects and derived work before acknowledging the input event."""
        needed = {"event_id", "object_id", "version", "content", "origin"}
        if not isinstance(event, dict) or not needed <= event.keys() or type(event["version"]) is not int or event["version"] < 1:
            raise ValueError("event fields or version are invalid")
        if any(not isinstance(event[k], str) or not event[k].strip()
               for k in ("event_id", "object_id", "content", "origin")):
            raise ValueError("event strings must be nonempty")
        if type(now) is not int or now < 0:
            raise ValueError("logical time must be a nonnegative integer")
        fingerprint = digest(event)
        existing = self.db.execute("SELECT * FROM events WHERE id=?", (event["event_id"],)).fetchone()
        if existing:
            if existing["digest"] != fingerprint:
                raise ValueError("event ID reused with a different payload")
            # A crash may have occurred after receive committed but before dispatch.
            # Resume ready durable work before ACK, including on duplicate delivery.
            self.flush(now)
            with self.db:
                self.db.execute("UPDATE events SET deliveries=deliveries+1,state='acked' WHERE id=?",
                                (event["event_id"],))
            self.record("duplicate_delivery", event_id=event["event_id"], decision=existing["decision"])
            return "duplicate"
        with self.db:
            current = self.db.execute("SELECT * FROM objects WHERE id=?", (event["object_id"],)).fetchone()
            if event["origin"] == "this-lab":
                decision = "self_event_ignored"
            elif current and event["version"] < current["version"]:
                decision = "stale"
            elif current and event["version"] == current["version"]:
                if event["content"] != current["content"] or current["conflicted"]:
                    decision = "version_conflict"
                    self.db.execute("UPDATE objects SET conflicted=1 WHERE id=?", (event["object_id"],))
                    self.db.execute("DELETE FROM pending WHERE object_id=? AND version=?",
                                    (event["object_id"], event["version"]))
                else:
                    decision = "same_version"
            else:
                # A trusted higher version resolves a quarantined version even
                # when its content equals the first, now-disputed observation.
                changed = not current or event["content"] != current["content"] or current["conflicted"]
                self.db.execute("INSERT INTO objects(id,version,content,conflicted) VALUES (?,?,?,0) ON CONFLICT(id) DO UPDATE SET "
                                "version=excluded.version,content=excluded.content,conflicted=0",
                                (event["object_id"], event["version"], event["content"]))
                decision = "changed" if changed else "unchanged_content"
                if changed:
                    for sub in self.db.execute("SELECT * FROM subscriptions WHERE active=1 AND object_id=?",
                                               (event["object_id"],)).fetchall():
                        if not sub["review_allowed"]:
                            self.record("business_authorization_denied", subscription=sub["id"])
                            continue
                        self.db.execute("INSERT INTO pending VALUES (?,?,?,?,?) ON CONFLICT(subscription) "
                                        "DO UPDATE SET version=excluded.version,content=excluded.content,"
                                        "ready_at=excluded.ready_at",
                                        (sub["id"], sub["object_id"], event["version"], event["content"], now+self.debounce))
                else:
                    # Preserve the newest source version of already-coalesced work,
                    # without creating a notification for an unchanged-only update.
                    self.db.execute("UPDATE pending SET version=? WHERE object_id=?",
                                    (event["version"], event["object_id"]))
            self.db.execute("INSERT INTO events VALUES (?,?,?,?,1)",
                            (event["event_id"], fingerprint, "processed", decision))
        self.record("event_processed", event_id=event["event_id"], decision=decision, now=now)
        if crash_after_receive:
            self.record("crash_after_receive", event_id=event["event_id"])
            raise SimulatedCrash("receive committed; dispatch has not run")
        self.flush(now)
        if crash_before_ack:
            self.record("crash_before_ack", event_id=event["event_id"])
            raise SimulatedCrash("durable effects committed; acknowledgement not recorded")
        with self.db:
            self.db.execute("UPDATE events SET state='acked' WHERE id=?", (event["event_id"],))
        return decision

    def flush(self, now):
        """Coalesce ready work. This is a local task acceptance transaction."""
        if type(now) is not int or now < 0:
            raise ValueError("logical time must be a nonnegative integer")
        with self.db:
            rows = self.db.execute("SELECT p.*,s.owner,s.active,s.review_allowed,s.notify,s.budget,s.used,"
                                   "o.conflicted,o.version AS current_version "
                                   "FROM pending p JOIN subscriptions s ON p.subscription=s.id "
                                   "JOIN objects o ON p.object_id=o.id WHERE ready_at<=?",
                                   (now,)).fetchall()
            for row in rows:
                self.db.execute("DELETE FROM pending WHERE subscription=?", (row["subscription"],))
                if (not row["active"] or not row["review_allowed"] or row["used"] >= row["budget"]
                        or row["conflicted"] or row["version"] != row["current_version"]):
                    self.record("dispatch_stopped", subscription=row["subscription"], reason="inactive_unauthorized_budget_or_source_conflict")
                    continue
                intent = f"review:{row['subscription']}:{row['object_id']}:v{row['version']}"
                run = "run-" + digest(intent)[:16]
                # The unique intent and task insert share the transaction with budget accounting.
                inserted = self.db.execute("INSERT OR IGNORE INTO tasks VALUES (?,?,?,?,?,?,?)",
                                           (intent, run, row["owner"], row["object_id"], row["version"], row["content"], "accepted")).rowcount
                if inserted:
                    self.db.execute("UPDATE subscriptions SET used=used+1 WHERE id=?", (row["subscription"],))
                    if row["notify"]:
                        self.db.execute("INSERT INTO outbox VALUES (?,?,?,?)",
                                        (intent, row["owner"], f"{row['object_id']} v{row['version']}: {row['content']}", "local_pending"))
                self.record("task_accepted", intent_id=intent, run_id=run, notification=bool(row["notify"]))

    def snapshot(self):
        return {name: [dict(row) for row in self.db.execute(f"SELECT * FROM {name} ORDER BY 1")]
                for name in ("subscriptions", "events", "objects", "pending", "tasks", "outbox")}


def event(identifier, version=2, content="普通员工住宿上限调整为700元", *, origin="policy-source"):
    return {"event_id": identifier, "object_id": "policy-hailan", "version": version,
            "content": content, "origin": origin}


SCENARIOS = ("normal", "duplicate", "out_of_order", "crash_recovery", "receive_recovery", "cancelled", "debounce", "conflict_resolution", "budget_and_loop", "authorization")


def run_scenario(name, directory):
    path = Path(directory) / "events.sqlite"
    receiver = Receiver(path, debounce=5 if name in ("debounce", "conflict_resolution") else 0)
    receiver.subscribe("s1", budget=1 if name == "budget_and_loop" else 2,
                       review_allowed=name != "authorization")
    if name == "normal":
        receiver.receive(event("e1"))
    elif name == "duplicate":
        receiver.receive(event("e1"))
        receiver.receive(event("e1"))
        receiver.receive(event("e2"))
    elif name == "out_of_order":
        receiver.receive(event("e3", 3, "上限750元"))
        receiver.receive(event("e2", 2, "上限700元"))
    elif name in ("crash_recovery", "receive_recovery"):
        try:
            receiver.receive(event("e1"), crash_before_ack=name == "crash_recovery",
                             crash_after_receive=name == "receive_recovery")
        except SimulatedCrash:
            prior_trace = receiver.trace[:]
            receiver.close()
            receiver = Receiver(path)
            receiver.trace = prior_trace
        receiver.receive(event("e1"))
    elif name == "cancelled":
        receiver.cancel("s1")
        receiver.receive(event("late-event"))
    elif name == "debounce":
        receiver.receive(event("e2"), now=0)
        receiver.receive(event("e3", 3, "上限750元"), now=2)
        receiver.flush(6)
        receiver.record("before_deadline", task_count=len(receiver.snapshot()["tasks"]))
        receiver.flush(7)
    elif name == "conflict_resolution":
        receiver.receive(event("e2", 2, "上限700元"), now=0)
        receiver.receive(event("conflicting-v2", 2, "上限999元"), now=1)
        receiver.flush(5)
        receiver.record("conflict_waiting", task_count=len(receiver.snapshot()["tasks"]))
        receiver.receive(event("resolved-v3", 3, "上限700元"), now=6)
        receiver.flush(11)
    elif name == "budget_and_loop":
        receiver.receive(event("e2"))
        receiver.receive(event("self", 8, "内部回写", origin="this-lab"))
        receiver.receive(event("e3", 3, "上限750元"))
    elif name == "authorization":
        receiver.receive(event("e2"))
    else:
        receiver.close()
        raise ValueError(name)
    snapshot, trace = receiver.snapshot(), receiver.trace
    receiver.close()
    expected = json.loads((Path(__file__).parent / "expected.json").read_text())[name]
    actual = {"tasks": len(snapshot["tasks"]), "outbox": len(snapshot["outbox"]),
              "version": snapshot["objects"][0]["version"] if snapshot["objects"] else None,
              "budget_used": snapshot["subscriptions"][0]["used"],
              "task_versions": [row["version"] for row in snapshot["tasks"]],
              "task_contents": [row["content"] for row in snapshot["tasks"]],
              "task_owners": [row["owner"] for row in snapshot["tasks"]],
              "outbox_states": [row["state"] for row in snapshot["outbox"]]}
    checks = {key: actual[key] == value for key, value in expected.items()}
    return {"scenario": name, "actual": actual, "checks": checks, "passed": all(checks.values()),
            "evidence_level": "local_sqlite_components", "snapshot": snapshot}, trace


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all",)+SCENARIOS, default="all")
    parser.add_argument("--output", type=Path, default=Path(".local/event_agent_lab/all-report.json"))
    args = parser.parse_args(argv)
    results, traces = [], []
    for name in SCENARIOS if args.scenario == "all" else (args.scenario,):
        with tempfile.TemporaryDirectory() as directory:
            result, trace = run_scenario(name, directory)
        results.append(result)
        traces.extend({"scenario": name, **item} for item in trace)
    passed = all(row["passed"] for row in results)
    report = {"passed": passed, "evidence_level": "local_sqlite_components", "external_delivery": False,
              "scenarios": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    (args.output.parent / "trace.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False)+"\n" for row in traces))
    (args.output.parent / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2)+"\n")
    (args.output.parent / "grade.json").write_text(json.dumps({"passed": passed, "checks": {r["scenario"]: r["checks"] for r in results}}, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"passed": passed, "scenarios": len(results), "report": str(args.output)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
