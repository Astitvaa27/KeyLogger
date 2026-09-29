"""Module 7 — Data storage (SQLite).

A thin, dependency-free persistence layer over the Python standard-library
``sqlite3`` module. The schema is deliberately flat and readable so the database
can be inspected directly:

    sqlite3 data/klab.sqlite3 ".tables"
    sqlite3 data/klab.sqlite3 "SELECT * FROM detections;"

Tables: test_sessions, events, process_observations, detections, risk_scores.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from klab.logging_setup import get_logger

log = get_logger("storage")

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    mode        TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    event_count INTEGER NOT NULL DEFAULT 0,
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    timestamp     TEXT NOT NULL,
    process_name  TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    event_count   INTEGER NOT NULL DEFAULT 0,
    key_category  TEXT,
    duration_ms   REAL,
    source        TEXT NOT NULL DEFAULT 'SIMULATED',
    persistence_indicator INTEGER NOT NULL DEFAULT 0,
    network_indicator     INTEGER NOT NULL DEFAULT 0,
    event_rate_per_min    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_events_session ON events(session_id);

CREATE TABLE IF NOT EXISTS process_observations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    timestamp     TEXT NOT NULL,
    pid           INTEGER NOT NULL,
    name          TEXT NOT NULL,
    ppid          INTEGER,
    cpu_percent   REAL,
    memory_mb     REAL,
    exe_path      TEXT,
    cmdline       TEXT,
    network_activity INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_proc_session ON process_observations(session_id);

CREATE TABLE IF NOT EXISTS detections (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        INTEGER NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    timestamp         TEXT NOT NULL,
    rule_id           TEXT NOT NULL,
    name              TEXT NOT NULL,
    severity          TEXT NOT NULL,
    evidence          TEXT NOT NULL,
    recommended_action TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_det_session ON detections(session_id);

CREATE TABLE IF NOT EXISTS risk_scores (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    timestamp    TEXT NOT NULL,
    score        INTEGER NOT NULL,
    level        TEXT NOT NULL,
    breakdown_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_risk_session ON risk_scores(session_id);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Storage:
    """SQLite-backed store. Use as a context manager or call close()."""

    db_path: Path
    _conn: sqlite3.Connection | None = None

    def __post_init__(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    # -- lifecycle ---------------------------------------------------------
    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Storage is closed")
        return self._conn

    def _init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)
        self.conn.execute(
            "INSERT OR IGNORE INTO schema_meta(key, value) VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self.conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "Storage":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    @contextmanager
    def _tx(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # -- sessions ----------------------------------------------------------
    def create_session(self, mode: str, notes: str | None = None) -> int:
        with self._tx() as c:
            cur = c.execute(
                "INSERT INTO test_sessions(mode, started_at, notes) VALUES(?,?,?)",
                (mode, _utcnow(), notes),
            )
            log.info("Created session #%s (mode=%s)", cur.lastrowid, mode)
            return int(cur.lastrowid)

    def end_session(self, session_id: int, event_count: int) -> None:
        with self._tx() as c:
            c.execute(
                "UPDATE test_sessions SET ended_at=?, event_count=? WHERE id=?",
                (_utcnow(), event_count, session_id),
            )

    def get_session(self, session_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM test_sessions WHERE id=?", (session_id,)
        ).fetchone()

    def latest_session_id(self) -> int | None:
        row = self.conn.execute(
            "SELECT id FROM test_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return int(row["id"]) if row else None

    def list_sessions(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM test_sessions ORDER BY id DESC"
        ).fetchall()

    # -- events ------------------------------------------------------------
    def add_events(self, session_id: int, events: list[dict]) -> int:
        rows = [
            (
                session_id,
                e.get("timestamp") or _utcnow(),
                e["process_name"],
                e["event_type"],
                int(e.get("event_count", 0)),
                e.get("key_category"),
                e.get("duration_ms"),
                e.get("source", "SIMULATED"),
                1 if e.get("persistence_indicator") else 0,
                1 if e.get("network_indicator") else 0,
                int(e.get("event_rate_per_min", 0)),
            )
            for e in events
        ]
        with self._tx() as c:
            c.executemany(
                """INSERT INTO events(
                    session_id, timestamp, process_name, event_type, event_count,
                    key_category, duration_ms, source, persistence_indicator,
                    network_indicator, event_rate_per_min)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                rows,
            )
        return len(rows)

    def get_events(self, session_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM events WHERE session_id=? ORDER BY id ASC", (session_id,)
        ).fetchall()

    # -- process observations ---------------------------------------------
    def add_process_observations(self, session_id: int, observations: list[dict]) -> int:
        rows = [
            (
                session_id,
                o.get("timestamp") or _utcnow(),
                int(o["pid"]),
                o["name"],
                o.get("ppid"),
                o.get("cpu_percent"),
                o.get("memory_mb"),
                o.get("exe_path"),
                o.get("cmdline"),
                1 if o.get("network_activity") else 0,
            )
            for o in observations
        ]
        with self._tx() as c:
            c.executemany(
                """INSERT INTO process_observations(
                    session_id, timestamp, pid, name, ppid, cpu_percent, memory_mb,
                    exe_path, cmdline, network_activity)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                rows,
            )
        return len(rows)

    def get_process_observations(self, session_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM process_observations WHERE session_id=? ORDER BY id ASC",
            (session_id,),
        ).fetchall()

    # -- detections --------------------------------------------------------
    def add_detections(self, session_id: int, detections: list[dict]) -> int:
        rows = [
            (
                session_id,
                d.get("timestamp") or _utcnow(),
                d["rule_id"],
                d["name"],
                d["severity"],
                d["evidence"],
                d["recommended_action"],
            )
            for d in detections
        ]
        with self._tx() as c:
            c.executemany(
                """INSERT INTO detections(
                    session_id, timestamp, rule_id, name, severity, evidence,
                    recommended_action)
                   VALUES(?,?,?,?,?,?,?)""",
                rows,
            )
        return len(rows)

    def get_detections(self, session_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM detections WHERE session_id=? ORDER BY id ASC", (session_id,)
        ).fetchall()

    # -- risk scores -------------------------------------------------------
    def add_risk_score(self, session_id: int, score: int, level: str, breakdown: dict) -> int:
        with self._tx() as c:
            cur = c.execute(
                """INSERT INTO risk_scores(session_id, timestamp, score, level, breakdown_json)
                   VALUES(?,?,?,?,?)""",
                (session_id, _utcnow(), score, level, json.dumps(breakdown)),
            )
            return int(cur.lastrowid)

    def latest_risk_score(self, session_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM risk_scores WHERE session_id=? ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()

    # -- aggregate counts (dashboard convenience) -------------------------
    def counts(self, session_id: int) -> dict:
        def n(sql: str) -> int:
            return int(self.conn.execute(sql, (session_id,)).fetchone()[0])

        return {
            "events": n("SELECT COUNT(*) FROM events WHERE session_id=?"),
            "observations": n("SELECT COUNT(*) FROM process_observations WHERE session_id=?"),
            "detections": n("SELECT COUNT(*) FROM detections WHERE session_id=?"),
        }
