"""Unit tests for the synthetic simulation service."""
from __future__ import annotations

from app.services.simulation import (
    ABNORMAL_EVENT_RATE,
    HIGH_KEYBOARD_VOLUME,
    generate_event,
    generate_events,
)


def test_generate_event_shape():
    ev = generate_event("balanced")
    assert set(ev) == {
        "process_name",
        "keyboard_events",
        "persistence_indicator",
        "network_activity",
        "event_rate_per_min",
        "risk_indicators",
    }
    assert isinstance(ev["risk_indicators"], list)


def test_indicators_are_consistent_with_values():
    for _ in range(50):
        ev = generate_event("aggressive")
        if ev["keyboard_events"] >= HIGH_KEYBOARD_VOLUME:
            assert "high_keyboard_event_volume" in ev["risk_indicators"]
        if ev["event_rate_per_min"] >= ABNORMAL_EVENT_RATE:
            assert "abnormal_event_frequency" in ev["risk_indicators"]
        if ev["persistence_indicator"] and ev["network_activity"]:
            assert "suspicious_process_behavior" in ev["risk_indicators"]


def test_generate_batch_count():
    events = generate_events(7, "benign")
    assert len(events) == 7


def test_benign_profile_is_low_risk_on_average():
    # Benign profile should rarely trigger the high-volume indicator.
    flagged = sum(
        1
        for _ in range(100)
        if "high_keyboard_event_volume" in generate_event("benign")["risk_indicators"]
    )
    assert flagged == 0
