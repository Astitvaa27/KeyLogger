"""Tests for Module 7 — SQLite storage."""
from __future__ import annotations

import pytest

from klab.storage import Storage


@pytest.fixture()
def store(tmp_path):
    with Storage(tmp_path / "t.sqlite3") as s:
        yield s


def test_session_lifecycle(store):
    sid = store.create_session("NORMAL_MODE", notes="unit")
    assert sid == 1
    assert store.latest_session_id() == sid
    store.end_session(sid, 3)
    row = store.get_session(sid)
    assert row["event_count"] == 3
    assert row["ended_at"] is not None


def test_events_and_counts(store):
    sid = store.create_session("HIGH_RISK_MODE")
    n = store.add_events(sid, [
        {"process_name": "demo-keylogger", "event_type": "KEYBOARD_ACTIVITY",
         "event_count": 100, "persistence_indicator": True, "network_indicator": True},
        {"process_name": "x", "event_type": "KEYBOARD_ACTIVITY", "event_count": 5},
    ])
    assert n == 2
    assert store.counts(sid)["events"] == 2
    rows = store.get_events(sid)
    assert rows[0]["persistence_indicator"] == 1  # bool stored as int


def test_detections_and_risk(store):
    sid = store.create_session("SUSPICIOUS_MODE")
    store.add_detections(sid, [
        {"rule_id": "KL-003", "name": "Persistence indicator", "severity": "HIGH",
         "evidence": "x", "recommended_action": "y"},
    ])
    store.add_risk_score(sid, 60, "HIGH", {"persistence": 25, "network": 25, "x": 10})
    assert store.counts(sid)["detections"] == 1
    risk = store.latest_risk_score(sid)
    assert risk["score"] == 60 and risk["level"] == "HIGH"


def test_process_observations(store):
    sid = store.create_session("NORMAL_MODE")
    n = store.add_process_observations(sid, [
        {"pid": 1, "name": "systemd", "network_activity": False},
        {"pid": 2, "name": "demo-keylogger", "network_activity": True},
    ])
    assert n == 2
    assert store.counts(sid)["observations"] == 2


def test_schema_persisted_across_reopen(tmp_path):
    db = tmp_path / "p.sqlite3"
    with Storage(db) as s:
        sid = s.create_session("NORMAL_MODE")
    with Storage(db) as s2:
        assert s2.get_session(sid) is not None
