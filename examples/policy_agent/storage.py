"""Two independent SQLite stores expose the commit/acknowledgment gap."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(payload: dict) -> str:
    return hashlib.sha256(canonical(payload).encode()).hexdigest()


class Stores:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with self.task_db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)")
        with self.service_db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS tickets (tenant_id TEXT NOT NULL, operation_id TEXT NOT NULL, payload_hash TEXT NOT NULL, body TEXT NOT NULL, UNIQUE(tenant_id, operation_id))")

    def task_db(self):
        return sqlite3.connect(self.run_dir / "task.sqlite")

    def service_db(self):
        return sqlite3.connect(self.run_dir / "service.sqlite")

    def save(self, state: dict):
        with self.task_db() as db:
            db.execute("INSERT INTO state VALUES (1,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body", (canonical(state),))

    def load(self) -> dict:
        with self.task_db() as db:
            row = db.execute("SELECT body FROM state WHERE id=1").fetchone()
        if row is None:
            raise ValueError("run has no saved state")
        return json.loads(row[0])

    def lookup(self, tenant_id: str, operation_id: str) -> dict | None:
        with self.service_db() as db:
            row = db.execute("SELECT body FROM tickets WHERE tenant_id=? AND operation_id=?", (tenant_id, operation_id)).fetchone()
        return json.loads(row[0]) if row else None

    def create(self, tenant_id: str, operation_id: str, payload: dict) -> tuple[dict, bool]:
        digest = fingerprint(payload)
        with self.service_db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload_hash,body FROM tickets WHERE tenant_id=? AND operation_id=?", (tenant_id, operation_id)).fetchone()
            if row:
                if row[0] != digest:
                    raise ValueError("idempotency_conflict: same operation has different full content")
                return json.loads(row[1]), True
            ticket = {"object_id": "OBJ-" + hashlib.sha256((tenant_id + ':' + operation_id).encode()).hexdigest()[:12], "operation_id": operation_id, "tenant_id": tenant_id, **payload}
            db.execute("INSERT INTO tickets VALUES (?,?,?,?)", (tenant_id, operation_id, digest, canonical(ticket)))
        return ticket, False

    def snapshot(self) -> list[dict]:
        with self.service_db() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT body FROM tickets ORDER BY operation_id")]
