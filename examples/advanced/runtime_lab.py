#!/usr/bin/env python3
"""Deterministic exercises for reliability estimates, budgets and durable replay."""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import tempfile


class BudgetExceeded(ValueError):
    pass


class SimulatedCrash(RuntimeError):
    pass


def pass_at_k(n: int, successes: int, k: int) -> float:
    if any(type(x) is not int for x in (n, successes, k)) or not 1 <= k <= n or not 0 <= successes <= n:
        raise ValueError("require integer 1 <= k <= n and 0 <= successes <= n")
    return 1.0 if n - successes < k else 1 - math.comb(n - successes, k) / math.comb(n, k)


def iid_reliability(probabilities: list[float], k: int) -> dict:
    if type(k) is not int or k < 1 or not probabilities:
        raise ValueError("nonempty probabilities and a positive integer k are required")
    if any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite numbers in [0, 1]")
    return {"mean_at_least_one": sum(1 - (1 - p) ** k for p in probabilities) / len(probabilities),
            "mean_all_succeed": sum(p ** k for p in probabilities) / len(probabilities)}


def relative_advantages(rewards: list[float]) -> list[float]:
    if not rewards or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in rewards):
        raise ValueError("finite numerical rewards are required")
    scale = max(abs(r) for r in rewards)
    if not scale:
        return [0.0] * len(rewards)
    # Standardization is invariant to positive scaling; avoid squaring tiny or huge rewards.
    scaled = [r / scale for r in rewards]
    mean = math.fsum(scaled) / len(scaled)
    variance = math.fsum((r - mean) ** 2 for r in scaled) / len(scaled)
    return [(r - mean) / math.sqrt(variance) for r in scaled] if variance else [0.0] * len(rewards)


class Budget:
    """One sequential ledger of reserved units, not model token billing."""

    def __init__(self, max_units: int, max_calls: int):
        if any(type(x) is not int or x < 1 for x in (max_units, max_calls)):
            raise ValueError("budget limits must be positive integers")
        self.max_units, self.max_calls = max_units, max_calls
        self.reservations: dict[str, int] = {}

    @property
    def used(self) -> int:
        return sum(self.reservations.values())

    def reserve(self, operation_id: str, units: int) -> None:
        if not isinstance(operation_id, str) or not operation_id or type(units) is not int or units < 1:
            raise ValueError("operation ID and positive integer units are required")
        if operation_id in self.reservations:
            if self.reservations[operation_id] != units:
                raise ValueError("reservation ID was reused with different units")
            return
        if self.used + units > self.max_units or len(self.reservations) + 1 > self.max_calls:
            raise BudgetExceeded("shared reservation budget exhausted")
        self.reservations[operation_id] = units


def critical_path(nodes: dict[str, tuple[int, list[str]]]) -> dict:
    """Earliest finish times under unlimited workers and fixed task durations."""
    visiting: set[str] = set()
    finish: dict[str, int] = {}

    def visit(name: str) -> int:
        if name not in nodes:
            raise ValueError(f"missing dependency: {name}")
        if name in visiting:
            raise ValueError("dependency graph contains a cycle")
        if name in finish:
            return finish[name]
        duration, dependencies = nodes[name]
        if type(duration) is not int or duration < 0:
            raise ValueError("durations must be nonnegative integer milliseconds")
        visiting.add(name)
        start = max((visit(parent) for parent in dependencies), default=0)
        visiting.remove(name)
        finish[name] = start + duration
        return finish[name]

    for name in nodes:
        visit(name)
    return {"parallel_lower_bound_ms": max(finish.values(), default=0),
            "serial_ms": sum(item[0] for item in nodes.values()), "finish_ms": finish}


def payload_hash(title: str) -> str:
    if not isinstance(title, str) or not title.strip():
        raise ValueError("a nonempty title is required")
    return hashlib.sha256(json.dumps({"title": title}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def remote_apply(path: Path, operation_id: str, title: str) -> int:
    """A separate SQLite backend with an atomic idempotency key contract."""
    if not isinstance(operation_id, str) or not operation_id:
        raise ValueError("a nonempty operation ID is required")
    digest = payload_hash(title)
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tickets (ticket_id INTEGER PRIMARY KEY, operation_id TEXT UNIQUE, digest TEXT, title TEXT)")
        conn.execute("INSERT INTO tickets(operation_id,digest,title) VALUES(?,?,?) ON CONFLICT(operation_id) DO NOTHING", (operation_id, digest, title))
        ticket_id, stored = conn.execute("SELECT ticket_id,digest FROM tickets WHERE operation_id=?", (operation_id,)).fetchone()
        if stored != digest:
            raise ValueError("remote operation ID conflicts with the stored payload")
    return ticket_id


def run_operation(local_path: Path, remote_path: Path, operation_id: str, title: str, *, crash_after_remote: bool = False) -> int:
    if not isinstance(operation_id, str) or not operation_id:
        raise ValueError("a nonempty operation ID is required")
    digest = payload_hash(title)
    with closing(sqlite3.connect(local_path)) as conn, conn:
        conn.execute("CREATE TABLE IF NOT EXISTS intents (operation_id TEXT PRIMARY KEY, digest TEXT, status TEXT, ticket_id INTEGER)")
        conn.execute("INSERT INTO intents VALUES(?,?,?,NULL) ON CONFLICT(operation_id) DO NOTHING", (operation_id, digest, "pending"))
        stored, status, ticket_id = conn.execute("SELECT digest,status,ticket_id FROM intents WHERE operation_id=?", (operation_id,)).fetchone()
        if stored != digest:
            raise ValueError("local operation ID conflicts with the stored payload")
    if status == "done":
        return ticket_id
    # The remote transaction commits independently of the local completion record.
    ticket_id = remote_apply(remote_path, operation_id, title)
    if crash_after_remote:
        raise SimulatedCrash("remote committed; local completion record not written")
    with closing(sqlite3.connect(local_path)) as conn, conn:
        conn.execute("UPDATE intents SET status='done',ticket_id=? WHERE operation_id=?", (ticket_id, operation_id))
    return ticket_id


def replay_demo() -> dict:
    with tempfile.TemporaryDirectory(prefix="agent-replay-") as directory:
        local, remote = Path(directory) / "local.sqlite", Path(directory) / "remote.sqlite"
        try:
            run_operation(local, remote, "intent-17", "Review policy evidence", crash_after_remote=True)
        except SimulatedCrash:
            pass
        with closing(sqlite3.connect(local)) as conn:
            before = conn.execute("SELECT status FROM intents").fetchone()[0]
        # Fresh database connections read the intent left by the interrupted run.
        recovered = run_operation(local, remote, "intent-17", "Review policy evidence")
        again = run_operation(local, remote, "intent-17", "Review policy evidence")
        with closing(sqlite3.connect(remote)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        with closing(sqlite3.connect(local)) as conn:
            after = conn.execute("SELECT status FROM intents").fetchone()[0]
        return {"status_after_crash": before, "status_after_resume": after,
                "ticket_after_resume": recovered, "ticket_after_replay": again, "remote_object_count": count}


def demo(name: str) -> dict:
    if name == "evaluation":
        return {"pass_at_2_from_1_of_5": pass_at_k(5, 1, 2),
                "heterogeneous_tasks_p": [0.9, 0.1], **iid_reliability([0.9, 0.1], 2),
                "relative_advantages": relative_advantages([0, 0, 1, 1])}
    if name == "budget":
        ledger = Budget(1000, 2)
        ledger.reserve("worker-a", 600)
        denied = False
        try:
            ledger.reserve("worker-b", 500)
        except BudgetExceeded:
            denied = True
        ledger.reserve("worker-b", 400)
        dag = {"plan": (200, []), "read-a": (300, ["plan"]), "read-b": (500, ["plan"]), "synthesize": (400, ["read-a", "read-b"])}
        return {"oversized_request_denied": denied, "reserved_units": ledger.used,
                "reservations": ledger.reservations, **critical_path(dag)}
    if name == "replay":
        return replay_demo()
    raise ValueError(f"unknown scenario: {name}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["all", "evaluation", "budget", "replay"], default="all")
    args = parser.parse_args(argv)
    for name in ("evaluation", "budget", "replay") if args.scenario == "all" else [args.scenario]:
        print(json.dumps({"scenario": name, **demo(name)}, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
