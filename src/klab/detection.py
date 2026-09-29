"""Module 4 — Keylogging detection engine.

A transparent, rule-based engine that inspects synthetic telemetry events and
read-only process observations and emits detections. Each rule maps to a named
risk indicator consumed by the risk engine (Module 5), so scoring is fully
explainable.

Rules:
    KL-001  Abnormal keyboard-event volume        (HIGH)
    KL-002  Suspicious process behaviour          (MEDIUM)
    KL-003  Persistence indicator                 (HIGH)
    KL-004  Unexpected network communication      (HIGH)
    KL-005  Abnormal process execution            (MEDIUM)
    KL-006  Suspicious combination of behaviours  (CRITICAL, meta-rule)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from klab.config import THRESHOLDS
from klab.logging_setup import get_logger

log = get_logger("detection")

# Process-name substrings that suggest input-monitoring behaviour.
_SUSPICIOUS_NAMES = ("keylog", "kbd-capture", "input-monitor", "demo-keylogger", "exfil")


@dataclass
class Detection:
    rule_id: str
    name: str
    severity: str
    evidence: str
    recommended_action: str
    indicator: str | None = None  # risk indicator key (None for meta-rules)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "severity": self.severity,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action,
            "timestamp": self.timestamp,
        }


# Static catalog (id -> metadata) for reporting/reference.
RULES = {
    "KL-001": {"name": "Abnormal keyboard-event volume", "severity": "HIGH",
               "indicator": "abnormal_event_volume"},
    "KL-002": {"name": "Suspicious process behaviour", "severity": "MEDIUM",
               "indicator": "suspicious_process_behavior"},
    "KL-003": {"name": "Persistence indicator", "severity": "HIGH",
               "indicator": "persistence"},
    "KL-004": {"name": "Unexpected network communication", "severity": "HIGH",
               "indicator": "network"},
    "KL-005": {"name": "Abnormal process execution", "severity": "MEDIUM",
               "indicator": "keyboard_monitoring"},
    "KL-006": {"name": "Suspicious combination of behaviours", "severity": "CRITICAL",
               "indicator": None},
}

_ACTIONS = {
    "KL-001": "Identify the process generating keyboard events and confirm it is an "
              "authorized input/accessibility tool; otherwise isolate it.",
    "KL-002": "Review the process name, path, and parent; validate it against a known-good "
              "software inventory.",
    "KL-003": "Audit autostart locations (systemd units, cron, ~/.config autostart, rc "
              "scripts) and remove unauthorized persistence.",
    "KL-004": "Inspect and, if unexpected, block the process's outbound connections; a "
              "monitor that also sends data is a likely exfiltration channel.",
    "KL-005": "Correlate the event rate with active user sessions; non-human rates suggest "
              "automated/hook-driven capture.",
    "KL-006": "Treat as high-priority: isolate the host and capture a forensic image before "
              "remediation.",
}


def _mk(rule_id: str, evidence: str) -> Detection:
    meta = RULES[rule_id]
    return Detection(
        rule_id=rule_id,
        name=meta["name"],
        severity=meta["severity"],
        evidence=evidence,
        recommended_action=_ACTIONS[rule_id],
        indicator=meta["indicator"],
    )


def analyze(events: list[dict], observations: list[dict] | None = None) -> list[Detection]:
    """Run all detection rules over telemetry events and process observations.

    ``events`` and ``observations`` are plain dicts (as stored/generated), so the
    engine works on both freshly generated data and rows loaded from SQLite.
    """
    observations = observations or []
    detections: list[Detection] = []

    if not events and not observations:
        return detections

    max_event_count = max((int(e.get("event_count", 0)) for e in events), default=0)
    max_rate = max((int(e.get("event_rate_per_min", 0)) for e in events), default=0)
    persistence_events = sum(1 for e in events if e.get("persistence_indicator"))
    network_events = sum(1 for e in events if e.get("network_indicator"))

    # An indicator must appear in a meaningful share of telemetry — not a single
    # stray event — before a HIGH detection fires. This keeps ordinary (NORMAL)
    # activity, where indicators are rare, reliably low-risk.
    min_events = max(3, len(events) // 10) if events else 1

    def _is_suspicious_name(name: str) -> bool:
        n = (name or "").lower()
        return any(k in n for k in _SUSPICIOUS_NAMES)

    suspicious_event_procs = {
        e.get("process_name") for e in events if _is_suspicious_name(e.get("process_name", ""))
    }
    suspicious_obs = [o for o in observations if _is_suspicious_name(o.get("name", ""))]
    # Only NOTEWORTHY observed processes count toward network detection, so
    # ordinary system processes with connections do not inflate the score.
    obs_network = [
        o for o in observations
        if o.get("network_activity") and _is_suspicious_name(o.get("name", ""))
    ]

    # KL-001 — abnormal keyboard-event volume
    thr_vol = THRESHOLDS["high_keyboard_event_volume"]
    if max_event_count >= thr_vol:
        detections.append(
            _mk("KL-001", f"peak event_count={max_event_count} (threshold {thr_vol})")
        )

    # KL-002 — suspicious process behaviour (by name, in telemetry or observations)
    if suspicious_event_procs or suspicious_obs:
        names = sorted(
            {n for n in suspicious_event_procs if n}
            | {o.get("name") for o in suspicious_obs}
        )
        detections.append(
            _mk("KL-002", f"suspicious process name(s): {', '.join(names)}")
        )

    # KL-003 — persistence indicator (needs a meaningful share of events)
    if persistence_events >= min_events:
        detections.append(
            _mk("KL-003", f"{persistence_events} event(s) carried a persistence indicator "
                          f"(min {min_events})")
        )

    # KL-004 — unexpected network communication
    if network_events >= min_events or obs_network:
        parts = []
        if network_events >= min_events:
            parts.append(f"{network_events} telemetry event(s) flagged network (min {min_events})")
        if obs_network:
            parts.append(f"{len(obs_network)} suspicious observed process(es) with connections")
        detections.append(_mk("KL-004", "; ".join(parts)))

    # KL-005 — abnormal process execution (non-human event rate)
    thr_rate = THRESHOLDS["abnormal_event_rate_per_min"]
    if max_rate >= thr_rate:
        detections.append(
            _mk("KL-005", f"peak event_rate_per_min={max_rate} (threshold {thr_rate})")
        )

    # KL-006 — suspicious combination of behaviours (meta-rule)
    strong_indicators = {
        d.indicator for d in detections if d.indicator in
        {"abnormal_event_volume", "persistence", "network", "keyboard_monitoring"}
    }
    if len(strong_indicators) >= 3:
        detections.append(
            _mk("KL-006", f"{len(strong_indicators)} strong indicators co-occur: "
                          f"{', '.join(sorted(strong_indicators))}")
        )

    log.info("Detection produced %d finding(s)", len(detections))
    return detections
