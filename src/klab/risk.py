"""Module 5 — Risk scoring.

Transparent, additive scoring. Each unique risk indicator raised by the
detection engine contributes a fixed weight; the sum (clamped to 0–100) maps to
a risk level. The engine reports exactly which indicators contributed and by how
much — the score is never a black box.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from klab.detection import Detection
from klab.logging_setup import get_logger

log = get_logger("risk")

# Indicator -> points. Mirrors the project's transparent scoring model.
RISK_WEIGHTS = {
    "keyboard_monitoring": 25,        # active keyboard-monitoring behaviour
    "persistence": 25,                # persistence indicator
    "network": 25,                    # network communication indicator
    "abnormal_event_volume": 15,      # abnormal keyboard-event volume
    "suspicious_process_behavior": 10,  # suspicious process behaviour
}

# Human-readable labels for each indicator (used in explanations/reports).
INDICATOR_LABELS = {
    "keyboard_monitoring": "Keyboard monitoring indicator",
    "persistence": "Persistence indicator",
    "network": "Network communication indicator",
    "abnormal_event_volume": "Abnormal keyboard-event volume",
    "suspicious_process_behavior": "Suspicious process behaviour",
}

_BANDS = (
    (0, 24, "LOW"),
    (25, 49, "MEDIUM"),
    (50, 74, "HIGH"),
    (75, 100, "CRITICAL"),
)


def level_for_score(score: int) -> str:
    for low, high, level in _BANDS:
        if low <= score <= high:
            return level
    return "CRITICAL"


@dataclass
class RiskResult:
    score: int
    level: str
    # ordered list of {indicator, label, points, rule_ids}
    contributions: list[dict] = field(default_factory=list)

    @property
    def breakdown(self) -> dict:
        """{indicator: points} — sums to `score` (transparency invariant)."""
        return {c["indicator"]: c["points"] for c in self.contributions}

    def explain_lines(self) -> list[str]:
        lines = []
        for c in self.contributions:
            rules = ", ".join(c["rule_ids"])
            lines.append(f"+{c['points']:>2}  {c['label']}  ({rules})")
        return lines


def score(detections: list[Detection]) -> RiskResult:
    """Compute a transparent risk score from detections."""
    # Gather, per indicator, which rules raised it.
    by_indicator: dict[str, list[str]] = {}
    for d in detections:
        if d.indicator and d.indicator in RISK_WEIGHTS:
            by_indicator.setdefault(d.indicator, []).append(d.rule_id)

    contributions: list[dict] = []
    total = 0
    # Emit in a stable, weight-descending order for readable breakdowns.
    for indicator in sorted(by_indicator, key=lambda k: (-RISK_WEIGHTS[k], k)):
        pts = RISK_WEIGHTS[indicator]
        total += pts
        contributions.append(
            {
                "indicator": indicator,
                "label": INDICATOR_LABELS[indicator],
                "points": pts,
                "rule_ids": sorted(set(by_indicator[indicator])),
            }
        )

    total = max(0, min(100, total))
    result = RiskResult(score=total, level=level_for_score(total), contributions=contributions)
    log.info("Risk score=%d level=%s (indicators=%d)", total, result.level, len(contributions))
    return result
