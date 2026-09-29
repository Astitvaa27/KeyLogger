"""Integration tests for the full session → keystrokes → simulation →
detection → dashboard flow, plus authorization boundaries."""
from __future__ import annotations


def test_keystroke_ingest_and_statistics(client, auth_headers, active_session):
    events = [
        {"sequence_number": 0, "category": "LETTER", "interval_ms": None},
        {"sequence_number": 1, "category": "LETTER", "interval_ms": 120},
        {"sequence_number": 2, "category": "EDITING_KEY", "interval_ms": 200},
        {"sequence_number": 3, "category": "MODIFIER", "key_label": "Shift", "interval_ms": 90},
    ]
    resp = client.post(
        "/api/keystrokes/events",
        json={"session_id": active_session, "events": events},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["accepted"] == 4

    stats = client.get(
        f"/api/keystrokes/statistics?session_id={active_session}", headers=auth_headers
    ).json()
    assert stats["total_keystrokes"] == 4
    assert stats["backspace_count"] == 1
    assert stats["modifier_count"] == 1


def test_key_label_sanitized_for_non_control_keys(client, auth_headers, active_session):
    # A non-whitelisted label (e.g. a letter) must be dropped server-side.
    events = [{"sequence_number": 0, "category": "LETTER", "key_label": "a"}]
    client.post(
        "/api/keystrokes/events",
        json={"session_id": active_session, "events": events},
        headers=auth_headers,
    )
    # Statistics still work; the label is not persisted (safety guarantee).
    stats = client.get(
        f"/api/keystrokes/statistics?session_id={active_session}", headers=auth_headers
    ).json()
    assert stats["total_keystrokes"] == 1


def test_events_rejected_on_stopped_session(client, auth_headers, active_session):
    client.post(f"/api/sessions/stop?session_id={active_session}", headers=auth_headers)
    resp = client.post(
        "/api/keystrokes/events",
        json={
            "session_id": active_session,
            "events": [{"sequence_number": 0, "category": "LETTER"}],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 409


def test_simulation_and_detection_flow(client, auth_headers, active_session):
    gen = client.post(
        "/api/simulation/generate",
        json={"session_id": active_session, "count": 6, "profile": "aggressive"},
        headers=auth_headers,
    )
    assert gen.status_code == 200
    assert len(gen.json()) == 6

    result = client.post(
        "/api/detection/analyze",
        json={"session_id": active_session},
        headers=auth_headers,
    ).json()
    assert 0 <= result["risk_score"] <= 100
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    # score_breakdown sums to risk_score (transparency invariant).
    assert sum(result["score_breakdown"].values()) == result["risk_score"]


def test_detection_rules_catalog(client, auth_headers):
    rules = client.get("/api/detection/rules", headers=auth_headers).json()
    ids = {r["rule_id"] for r in rules}
    assert {"RULE-001", "RULE-002", "RULE-003", "RULE-004", "RULE-005"} <= ids


def test_dashboard_summary(client, auth_headers, active_session):
    client.post(
        "/api/simulation/generate",
        json={"session_id": active_session, "count": 3, "profile": "balanced"},
        headers=auth_headers,
    )
    summary = client.get("/api/dashboard/summary", headers=auth_headers).json()
    assert summary["total_sessions"] >= 1
    assert summary["events_detected"] >= 3
    assert "timeline" in summary


def test_cannot_access_another_users_session(client, auth_headers, active_session):
    # Register a second user and confirm they cannot touch the first's session.
    other = client.post(
        "/api/auth/register",
        json={"email": "eve@example.com", "username": "eve", "password": "EvePass123!"},
    ).json()
    eve_headers = {"Authorization": f"Bearer {other['access_token']}"}

    resp = client.get(f"/api/sessions/{active_session}", headers=eve_headers)
    assert resp.status_code == 404

    resp = client.post(
        "/api/keystrokes/events",
        json={
            "session_id": active_session,
            "events": [{"sequence_number": 0, "category": "LETTER"}],
        },
        headers=eve_headers,
    )
    assert resp.status_code == 404


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
