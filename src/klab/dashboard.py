"""Module 6 — Terminal dashboard.

Renders a compact SOC-style console view for a session: system status, detection
status, counts, risk score/level, and recent detection events. Uses only the
stdlib UI helpers so it works over any terminal (no extra dependencies).
"""
from __future__ import annotations

from klab import ui
from klab.config import LabContext
from klab.environment import collect_environment
from klab.storage import Storage


def render_session(ctx: LabContext, store: Storage, session_id: int) -> str:
    """Return the dashboard as a string (also printed by the caller)."""
    session = store.get_session(session_id)
    counts = store.counts(session_id)
    detections = [dict(r) for r in store.get_detections(session_id)]
    risk = store.latest_risk_score(session_id)
    env = collect_environment(include_processes=True)

    score = int(risk["score"]) if risk else 0
    level = risk["level"] if risk else "LOW"

    suspicious_procs = len({d["evidence"] for d in detections if d["rule_id"] == "KL-002"})
    lab_procs = len(env.lab_processes)

    lines: list[str] = []
    lines.append(ui.banner("LINUX KEYLOGGING DEFENSE LAB"))
    lines.append("")

    lines.append(ui.header("System Status"))
    lines.append(ui.kv("Host / Distro", f"{env.hostname}  ·  {env.distribution}"))
    lines.append(ui.kv("Kernel", f"{env.os_system} {env.os_release}"))
    lines.append(ui.kv("Session", f"#{session_id}  ·  mode={session['mode'] if session else '?'}"))

    lines.append(ui.header("Detection Status"))
    status = ui.color("ATTENTION", "red") if score >= 50 else (
        ui.color("ELEVATED", "yellow") if score >= 25 else ui.color("NOMINAL", "green"))
    lines.append(ui.kv("Status", status))
    lines.append(ui.kv("Events Processed", counts["events"]))
    lines.append(ui.kv("Process Observations", counts["observations"]))
    lines.append(ui.kv("Suspicious Processes", suspicious_procs))
    lines.append(ui.kv("Lab-relevant Processes", lab_procs))
    lines.append(ui.kv("Detections", counts["detections"]))

    lines.append(ui.header("Risk"))
    bar_len = 30
    filled = int(round(score / 100 * bar_len))
    bar = "█" * filled + "░" * (bar_len - filled)
    lines.append(ui.kv("Risk Score", f"{ui.color(str(score), ui.LEVEL_COLORS.get(level,'cyan'))} / 100"))
    lines.append(ui.kv("Risk Level", ui.level_tag(level)))
    lines.append(ui.kv("", ui.color(bar, ui.LEVEL_COLORS.get(level, "cyan"))))

    lines.append(ui.header("Recent Detection Events"))
    if not detections:
        lines.append(ui.info("No detections for this session."))
    else:
        for d in detections[-8:]:
            lines.append(f"  {ui.level_tag(d['severity'])} {ui.bold(d['rule_id'])}  {d['name']}")
            lines.append(ui.color(f"      {d['evidence']}", "grey"))

    if risk:
        lines.append(ui.header("Why this score"))
        import json as _json
        breakdown = _json.loads(risk["breakdown_json"])
        if breakdown:
            for indicator, pts in sorted(breakdown.items(), key=lambda kv: -kv[1]):
                lines.append(f"  +{pts:>2}  {indicator}")
        else:
            lines.append(ui.info("No risk indicators contributed (LOW)."))

    return "\n".join(lines)
