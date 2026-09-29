"""Rule-based keylogging detection engine and transparent risk scoring.

The engine is intentionally NOT a black box: every rule that fires reports its
id, severity, the concrete evidence that triggered it, a recommendation, and
the exact number of points it contributed to the final risk score.

It analyzes the SYNTHETIC simulation telemetry produced by the simulation
service (and, optionally, aggregate keystroke-lab metadata). It never inspects
real system processes.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.models.enums import RiskLevel, Severity
from app.models.simulation import SimulationEvent
from app.services.simulation import ABNORMAL_EVENT_RATE, HIGH_KEYBOARD_VOLUME

# ---------------------------------------------------------------------------
# Rule catalog. Each rule maps to a synthetic risk indicator and a weight.
# These weights define the transparent scoring model.
# ---------------------------------------------------------------------------
RULES: dict[str, dict] = {
    "RULE-001": {
        "name": "High keyboard event volume",
        "description": "Process reports an unusually high volume of keyboard events.",
        "severity": Severity.HIGH,
        "weight": 25,
        "indicator": "high_keyboard_event_volume",
        "recommendation": (
            "Investigate the process capturing keyboard input; validate whether "
            "it is an authorized accessibility or input tool."
        ),
    },
    "RULE-002": {
        "name": "Suspicious persistence indicator",
        "description": "Process exhibits persistence (auto-start / re-launch) behavior.",
        "severity": Severity.HIGH,
        "weight": 25,
        "indicator": "persistence_indicator",
        "recommendation": (
            "Audit auto-start locations (registry run keys, scheduled tasks, "
            "services, launch agents) and remove unauthorized persistence."
        ),
    },
    "RULE-003": {
        "name": "Unexpected network communication",
        "description": "Input-capturing process is also communicating over the network.",
        "severity": Severity.CRITICAL,
        "weight": 25,
        "indicator": "network_communication",
        "recommendation": (
            "Block and investigate outbound connections from the process; a "
            "keylogger that also sends data is a likely exfiltration channel."
        ),
    },
    "RULE-004": {
        "name": "Abnormal event frequency",
        "description": "Keyboard event rate exceeds a normal human-typing baseline.",
        "severity": Severity.MEDIUM,
        "weight": 15,
        "indicator": "abnormal_event_frequency",
        "recommendation": (
            "Correlate the event rate with active user sessions; automated or "
            "hook-driven capture often produces non-human rates."
        ),
    },
    "RULE-005": {
        "name": "Suspicious process behavior",
        "description": "Process combines multiple risk behaviors (persistence + network).",
        "severity": Severity.MEDIUM,
        "weight": 10,
        "indicator": "suspicious_process_behavior",
        "recommendation": (
            "Treat the process as high priority for containment; isolate the host "
            "and capture a forensic image before remediation."
        ),
    },
}

# Risk-level bands from the cumulative score (0–100, clamped).
_RISK_BANDS = (
    (0, 24, RiskLevel.LOW),
    (25, 49, RiskLevel.MEDIUM),
    (50, 74, RiskLevel.HIGH),
    (75, 100, RiskLevel.CRITICAL),
)


def _level_for_score(score: int) -> RiskLevel:
    for low, high, level in _RISK_BANDS:
        if low <= score <= high:
            return level
    return RiskLevel.CRITICAL


def _evidence_for(indicator: str, agg: dict) -> str:
    """Build a concrete, human-readable evidence string for a fired rule."""
    if indicator == "high_keyboard_event_volume":
        return (
            f"max keyboard_events={agg['max_keyboard_events']} "
            f"(threshold {HIGH_KEYBOARD_VOLUME})"
        )
    if indicator == "persistence_indicator":
        return f"{agg['persistence_count']} event(s) reported persistence"
    if indicator == "network_communication":
        return f"{agg['network_count']} event(s) reported network activity"
    if indicator == "abnormal_event_frequency":
        return (
            f"max event_rate_per_min={agg['max_event_rate']} "
            f"(threshold {ABNORMAL_EVENT_RATE})"
        )
    if indicator == "suspicious_process_behavior":
        return (
            f"{agg['combined_count']} event(s) combined persistence + network"
        )
    return "indicator present"


def _aggregate(events: list[SimulationEvent]) -> dict:
    """Aggregate synthetic telemetry into the fields the rules examine."""
    indicators: set[str] = set()
    for e in events:
        indicators.update(e.risk_indicators or [])
    return {
        "present_indicators": indicators,
        "max_keyboard_events": max((e.keyboard_events for e in events), default=0),
        "max_event_rate": max((e.event_rate_per_min for e in events), default=0),
        "persistence_count": sum(1 for e in events if e.persistence_indicator),
        "network_count": sum(1 for e in events if e.network_activity),
        "combined_count": sum(
            1 for e in events if e.persistence_indicator and e.network_activity
        ),
    }


def analyze(events: list[SimulationEvent]) -> dict:
    """Run all rules over the synthetic telemetry and compute a risk score.

    Returns a dict with `risk_score`, `risk_level`, `triggered_rules`
    (full breakdown) and `score_breakdown` ({rule_id: points}).
    """
    agg = _aggregate(events)
    present = agg["present_indicators"]
    now = datetime.now(timezone.utc)

    triggered: list[dict] = []
    breakdown: dict[str, int] = {}
    score = 0

    for rule_id, rule in RULES.items():
        if rule["indicator"] in present:
            contribution = rule["weight"]
            score += contribution
            breakdown[rule_id] = contribution
            triggered.append(
                {
                    "rule_id": rule_id,
                    "name": rule["name"],
                    "description": rule["description"],
                    "severity": rule["severity"].value,
                    "evidence": _evidence_for(rule["indicator"], agg),
                    "recommendation": rule["recommendation"],
                    "contribution": contribution,
                    "timestamp": now.isoformat(),
                }
            )

    score = max(0, min(100, score))
    return {
        "risk_score": score,
        "risk_level": _level_for_score(score),
        "triggered_rules": triggered,
        "score_breakdown": breakdown,
    }
