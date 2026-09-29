"""Tests for Module 4 (detection) and Module 5 (risk)."""
from __future__ import annotations

from klab.config import ExperimentMode
from klab.detection import analyze
from klab.risk import RISK_WEIGHTS, level_for_score, score
from klab.telemetry import generate_batch


def _events(**over):
    base = {
        "process_name": "user-app", "event_type": "KEYBOARD_ACTIVITY", "event_count": 10,
        "key_category": "ALPHANUMERIC", "persistence_indicator": False,
        "network_indicator": False, "event_rate_per_min": 20,
    }
    base.update(over)
    return base


def test_no_data_no_detections():
    assert analyze([], []) == []


def test_kl001_volume():
    events = [_events(event_count=5000) for _ in range(5)]
    dets = {d.rule_id for d in analyze(events, [])}
    assert "KL-001" in dets


def test_kl003_persistence_requires_share():
    # A single stray persistence event must NOT trigger (min share rule).
    events = [_events() for _ in range(20)]
    events[0]["persistence_indicator"] = True
    assert "KL-003" not in {d.rule_id for d in analyze(events, [])}
    # Many persistence events DO trigger.
    for e in events:
        e["persistence_indicator"] = True
    assert "KL-003" in {d.rule_id for d in analyze(events, [])}


def test_kl002_suspicious_process_name():
    events = [_events(process_name="demo-keylogger") for _ in range(5)]
    assert "KL-002" in {d.rule_id for d in analyze(events, [])}


def test_kl004_only_counts_suspicious_observations():
    events = [_events() for _ in range(10)]
    # ordinary process with network should NOT trigger KL-004
    obs_ordinary = [{"pid": 1, "name": "firefox", "network_activity": True}]
    assert "KL-004" not in {d.rule_id for d in analyze(events, obs_ordinary)}
    # suspicious-named process with network SHOULD trigger KL-004
    obs_susp = [{"pid": 2, "name": "demo-keylogger", "network_activity": True}]
    assert "KL-004" in {d.rule_id for d in analyze(events, obs_susp)}


def test_risk_breakdown_sums_to_score():
    events = generate_batch(ExperimentMode.HIGH_RISK, 40, seed=1)
    r = score(analyze(events, []))
    assert sum(r.breakdown.values()) == r.score
    assert r.level == "CRITICAL"


def test_mode_separation_deterministic():
    normal = score(analyze(generate_batch(ExperimentMode.NORMAL, 50, seed=2), []))
    susp = score(analyze(generate_batch(ExperimentMode.SUSPICIOUS, 50, seed=2), []))
    high = score(analyze(generate_batch(ExperimentMode.HIGH_RISK, 50, seed=2), []))
    assert normal.level == "LOW"
    assert susp.level in ("MEDIUM", "HIGH")
    assert high.level == "CRITICAL"
    assert normal.score < susp.score < high.score or (susp.score < high.score)


def test_level_bands():
    assert level_for_score(0) == "LOW"
    assert level_for_score(24) == "LOW"
    assert level_for_score(25) == "MEDIUM"
    assert level_for_score(49) == "MEDIUM"
    assert level_for_score(50) == "HIGH"
    assert level_for_score(74) == "HIGH"
    assert level_for_score(75) == "CRITICAL"
    assert level_for_score(100) == "CRITICAL"


def test_weights_are_transparent():
    # The documented model: 25/25/25/15/10.
    assert sorted(RISK_WEIGHTS.values(), reverse=True) == [25, 25, 25, 15, 10]
