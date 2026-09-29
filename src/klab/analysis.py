"""Module 8 — Analysis and dataset export.

Computes descriptive analytics over a session's telemetry, process observations,
detections, and risk scores, and exports reproducible CSV/JSON datasets for
experiments.

Analyses: event frequency, event bursts, inter-event intervals, process
behaviour summary, detection frequency, and risk trend.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from statistics import mean, median

from klab.logging_setup import get_logger
from klab.storage import Storage

log = get_logger("analysis")


def _parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _intervals_seconds(timestamps: list[str]) -> list[float]:
    parsed = [t for t in (_parse_ts(x) for x in timestamps) if t is not None]
    parsed.sort()
    return [
        (parsed[i] - parsed[i - 1]).total_seconds() for i in range(1, len(parsed))
    ]


def analyze_session(store: Storage, session_id: int, burst_threshold: int = 500) -> dict:
    """Produce a structured analytics summary for a session."""
    events = [dict(r) for r in store.get_events(session_id)]
    observations = [dict(r) for r in store.get_process_observations(session_id)]
    detections = [dict(r) for r in store.get_detections(session_id)]
    risk = store.latest_risk_score(session_id)

    event_counts = [int(e.get("event_count", 0)) for e in events]
    rates = [int(e.get("event_rate_per_min", 0)) for e in events]
    intervals = _intervals_seconds([e.get("timestamp", "") for e in events])

    # Event frequency by process and by key category.
    by_process: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for e in events:
        by_process[e.get("process_name", "?")] = by_process.get(e.get("process_name", "?"), 0) + 1
        cat = e.get("key_category") or "UNKNOWN"
        by_category[cat] = by_category.get(cat, 0) + 1

    # Event bursts: events whose event_count exceeds the burst threshold.
    bursts = [
        {"process_name": e.get("process_name"), "event_count": int(e.get("event_count", 0)),
         "timestamp": e.get("timestamp")}
        for e in events
        if int(e.get("event_count", 0)) >= burst_threshold
    ]

    # Detection frequency by rule and by severity.
    det_by_rule: dict[str, int] = {}
    det_by_sev: dict[str, int] = {}
    for d in detections:
        det_by_rule[d["rule_id"]] = det_by_rule.get(d["rule_id"], 0) + 1
        det_by_sev[d["severity"]] = det_by_sev.get(d["severity"], 0) + 1

    summary = {
        "session_id": session_id,
        "totals": {
            "events": len(events),
            "observations": len(observations),
            "detections": len(detections),
            "total_keyboard_events": sum(event_counts),
        },
        "event_frequency": {
            "by_process": by_process,
            "by_key_category": by_category,
        },
        "event_volume": {
            "min": min(event_counts) if event_counts else 0,
            "max": max(event_counts) if event_counts else 0,
            "mean": round(mean(event_counts), 2) if event_counts else 0,
            "median": round(median(event_counts), 2) if event_counts else 0,
        },
        "event_rate_per_min": {
            "min": min(rates) if rates else 0,
            "max": max(rates) if rates else 0,
            "mean": round(mean(rates), 2) if rates else 0,
        },
        "inter_event_interval_seconds": {
            "count": len(intervals),
            "mean": round(mean(intervals), 3) if intervals else 0,
            "median": round(median(intervals), 3) if intervals else 0,
        },
        "bursts": {"threshold": burst_threshold, "count": len(bursts), "items": bursts[:20]},
        "detection_frequency": {"by_rule": det_by_rule, "by_severity": det_by_sev},
        "risk": {
            "score": int(risk["score"]) if risk else 0,
            "level": risk["level"] if risk else "LOW",
            "breakdown": json.loads(risk["breakdown_json"]) if risk else {},
        },
    }
    log.info("Analyzed session #%s: %d events, %d detections", session_id,
             len(events), len(detections))
    return summary


# ---- Exporters -----------------------------------------------------------
def export_json(summary: dict, out_dir: Path, session_id: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"session_{session_id}_analysis.json"
    path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    return path


def export_events_csv(store: Storage, out_dir: Path, session_id: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"session_{session_id}_events.csv"
    events = [dict(r) for r in store.get_events(session_id)]
    fields = [
        "id", "session_id", "timestamp", "process_name", "event_type", "event_count",
        "key_category", "duration_ms", "source", "persistence_indicator",
        "network_indicator", "event_rate_per_min",
    ]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for e in events:
            writer.writerow(e)
    return path


def export_detections_csv(store: Storage, out_dir: Path, session_id: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"session_{session_id}_detections.csv"
    dets = [dict(r) for r in store.get_detections(session_id)]
    fields = ["id", "session_id", "timestamp", "rule_id", "name", "severity",
              "evidence", "recommended_action"]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for d in dets:
            writer.writerow(d)
    return path


def export_all(store: Storage, summary: dict, out_dir: Path, session_id: int) -> list[Path]:
    return [
        export_json(summary, out_dir, session_id),
        export_events_csv(store, out_dir, session_id),
        export_detections_csv(store, out_dir, session_id),
    ]
