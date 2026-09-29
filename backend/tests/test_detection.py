"""Unit tests for the detection engine and risk scoring."""
from __future__ import annotations

from app.models.enums import RiskLevel
from app.models.simulation import SimulationEvent
from app.services.detection import RULES, analyze


def _event(**kwargs):
    defaults = dict(
        session_id=1,
        process_name="demo-keylogger.exe",
        keyboard_events=0,
        persistence_indicator=False,
        network_activity=False,
        event_rate_per_min=0,
        risk_indicators=[],
    )
    defaults.update(kwargs)
    return SimulationEvent(**defaults)


def test_no_events_is_low_risk():
    result = analyze([])
    assert result["risk_score"] == 0
    assert result["risk_level"] == RiskLevel.LOW
    assert result["triggered_rules"] == []


def test_single_indicator_scores_its_weight():
    ev = _event(
        keyboard_events=5000,
        risk_indicators=["high_keyboard_event_volume"],
    )
    result = analyze([ev])
    assert result["risk_score"] == RULES["RULE-001"]["weight"]
    assert result["risk_level"] == RiskLevel.MEDIUM  # 25 -> MEDIUM band
    assert result["score_breakdown"] == {"RULE-001": 25}


def test_all_indicators_reach_critical_and_clamp():
    ev = _event(
        keyboard_events=6000,
        persistence_indicator=True,
        network_activity=True,
        event_rate_per_min=900,
        risk_indicators=[
            "high_keyboard_event_volume",
            "persistence_indicator",
            "network_communication",
            "abnormal_event_frequency",
            "suspicious_process_behavior",
        ],
    )
    result = analyze([ev])
    assert result["risk_score"] == 100  # 25+25+25+15+10
    assert result["risk_level"] == RiskLevel.CRITICAL
    assert len(result["triggered_rules"]) == 5
    # Transparency: every triggered rule carries evidence + recommendation.
    for rule in result["triggered_rules"]:
        assert rule["evidence"]
        assert rule["recommendation"]
        assert rule["contribution"] > 0


def test_risk_bands():
    # Persistence(25)+abnormal(15) = 40 -> MEDIUM
    ev = _event(
        persistence_indicator=True,
        event_rate_per_min=500,
        risk_indicators=["persistence_indicator", "abnormal_event_frequency"],
    )
    result = analyze([ev])
    assert result["risk_score"] == 40
    assert result["risk_level"] == RiskLevel.MEDIUM
