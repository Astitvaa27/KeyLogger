"""Module 9 — PDF report generation.

Produces a professional, multi-section PDF experiment report for a session using
fpdf2 (a pure-Python dependency). If fpdf2 is unavailable, a Markdown fallback is
written so `report` never hard-fails.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from klab import __title__, __version__
from klab.config import LabContext
from klab.detection import RULES as DETECTION_RULES
from klab.logging_setup import get_logger
from klab.risk import RISK_WEIGHTS
from klab.storage import Storage

log = get_logger("report")

try:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    _HAS_FPDF = True
except Exception:  # pragma: no cover
    _HAS_FPDF = False


_UNICODE_MAP = {
    "—": "-",   # em dash
    "–": "-",   # en dash
    "‘": "'", "’": "'",  # curly single quotes
    "“": '"', "”": '"',  # curly double quotes
    "→": "->",  # right arrow
    "…": "...",  # ellipsis
    "·": "-",   # middle dot
    "•": "-",   # bullet
}


def _s(text) -> str:
    """Make text safe for the latin-1 core PDF font."""
    s = str(text)
    for uni, ascii_ in _UNICODE_MAP.items():
        s = s.replace(uni, ascii_)
    return s.encode("latin-1", "replace").decode("latin-1")


_SECTIONS = [
    "Experiment Overview",
    "Objective",
    "Linux VM Environment",
    "Architecture",
    "Threat Model",
    "Test Methodology",
    "Generated Telemetry",
    "Detection Rules",
    "Detection Results",
    "Risk Analysis",
    "Screenshots",
    "Defensive Recommendations",
    "Limitations",
    "Future Scope",
    "Conclusion",
]


def _gather(ctx: LabContext, store: Storage, session_id: int, summary: dict) -> dict:
    session = store.get_session(session_id)
    detections = [dict(r) for r in store.get_detections(session_id)]
    return {
        "session": dict(session) if session else {},
        "detections": detections,
        "summary": summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


class _Pdf(FPDF if _HAS_FPDF else object):  # type: ignore[misc]
    def header(self):  # pragma: no cover - visual
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120)
        self.cell(0, 6, _s("Linux Keylogging Defense Lab - Experiment Report"),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_text_color(0)
        self.ln(2)

    def footer(self):  # pragma: no cover - visual
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150)
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="C")
        self.set_text_color(0)


def _h1(pdf, text: str) -> None:
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(15, 26, 46)
    pdf.set_text_color(255)
    pdf.cell(0, 9, _s(f"  {text}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    pdf.set_text_color(0)
    pdf.ln(2)


def _p(pdf, text: str) -> None:
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.2, _s(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def _kv(pdf, key: str, value: str) -> None:
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(55, 5.5, _s(key))
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.5, _s(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _build_pdf(data: dict, ctx: LabContext, out_path: Path) -> Path:  # pragma: no cover
    summary = data["summary"]
    session = data["session"]

    pdf = _Pdf()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title block
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(0, 9, _s(__title__), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90)
    pdf.multi_cell(0, 5.5, _s(f"Version {__version__}  -  Generated {data['generated_at']}"),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0)
    pdf.ln(3)

    risk = summary.get("risk", {})
    totals = summary.get("totals", {})

    # 1. Experiment Overview
    _h1(pdf, "1. Experiment Overview")
    _p(pdf, "This report documents a defensive keylogging experiment executed inside an "
            "isolated, authorized Linux VM. The lab generates synthetic keylogging "
            "telemetry, performs read-only process observation, runs a transparent "
            "rule-based detection engine, and computes an explainable risk score. No real "
            "keystrokes, credentials, or user input are captured at any point.")
    _kv(pdf, "Session ID", session.get("id", "?"))
    _kv(pdf, "Experiment mode", session.get("mode", "?"))
    _kv(pdf, "Started", session.get("started_at", "?"))
    _kv(pdf, "Ended", session.get("ended_at", "?"))

    # 2. Objective
    _h1(pdf, "2. Objective")
    _p(pdf, "Demonstrate how a defensive system distinguishes ordinary activity from "
            "suspicious keylogging-like behaviour, and quantify the resulting risk in a "
            "transparent, reproducible way.")

    # 3. Linux VM Environment
    _h1(pdf, "3. Linux VM Environment")
    _kv(pdf, "Total events", totals.get("events", 0))
    _kv(pdf, "Process observations", totals.get("observations", 0))
    _kv(pdf, "Detections", totals.get("detections", 0))
    _p(pdf, "Environment metadata (host, kernel, distribution, CPU/memory) is captured by "
            "Module 1 at runtime and shown via `python main.py status`.")

    # 4. Architecture
    _h1(pdf, "4. Architecture")
    _p(pdf, "CLI-first pipeline: Test Environment -> Synthetic Telemetry -> Behaviour "
            "Monitor -> Detection Engine -> Risk Scoring -> Storage -> Analysis -> "
            "Dashboard / Report. Each stage is an independent, unit-tested Python module.")

    # 5. Threat Model
    _h1(pdf, "5. Threat Model")
    _p(pdf, "All attack behaviour is simulated. System interaction is limited to read-only "
            "/proc metadata. The framework implements no input capture, persistence, "
            "stealth, privilege escalation, or exfiltration. See docs/threat-model.md.")

    # 6. Test Methodology
    _h1(pdf, "6. Test Methodology")
    _p(pdf, "A test session generates a batch of synthetic telemetry biased by the selected "
            "experiment mode (NORMAL, SUSPICIOUS, HIGH_RISK), snapshots running processes "
            "read-only, runs all detection rules, and scores risk. Results are persisted to "
            "SQLite for inspection and export.")

    # 7. Generated Telemetry
    _h1(pdf, "7. Generated Telemetry")
    ev = summary.get("event_volume", {})
    rt = summary.get("event_rate_per_min", {})
    _kv(pdf, "Total keyboard events", totals.get("total_keyboard_events", 0))
    _kv(pdf, "Event count (min/mean/max)", f"{ev.get('min',0)} / {ev.get('mean',0)} / {ev.get('max',0)}")
    _kv(pdf, "Event rate/min (max)", rt.get("max", 0))
    by_proc = summary.get("event_frequency", {}).get("by_process", {})
    if by_proc:
        _p(pdf, "Events by process: " + ", ".join(f"{k}={v}" for k, v in by_proc.items()))

    # 8. Detection Rules
    _h1(pdf, "8. Detection Rules")
    for rid, meta in DETECTION_RULES.items():
        _kv(pdf, rid, f"{meta['name']}  [{meta['severity']}]")

    # 9. Detection Results
    _h1(pdf, "9. Detection Results")
    if data["detections"]:
        for d in data["detections"]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 5.2, _s(f"[{d['severity']}] {d['rule_id']} - {d['name']}"),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(70)
            pdf.multi_cell(0, 4.8, _s(f"Evidence: {d['evidence']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.multi_cell(0, 4.8, _s(f"Action: {d['recommended_action']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0)
            pdf.ln(1)
    else:
        _p(pdf, "No detections fired for this session (consistent with a LOW-risk baseline).")

    # 10. Risk Analysis
    _h1(pdf, "10. Risk Analysis")
    _kv(pdf, "Risk score", f"{risk.get('score', 0)} / 100")
    _kv(pdf, "Risk level", risk.get("level", "LOW"))
    breakdown = risk.get("breakdown", {})
    if breakdown:
        _p(pdf, "Transparent contribution breakdown (indicator -> points):")
        for indicator, pts in sorted(breakdown.items(), key=lambda kv: -kv[1]):
            _kv(pdf, f"  {indicator}", f"+{pts}")
    else:
        _p(pdf, "No risk indicators contributed; the score is 0 (LOW).")
    _p(pdf, "Scoring weights: " + ", ".join(f"{k}=+{v}" for k, v in RISK_WEIGHTS.items()))

    # 11. Screenshots
    _h1(pdf, "11. Screenshots")
    _p(pdf, "Placeholder — attach terminal captures of `status`, `test`, and the dashboard "
            "here for your submission (see docs/screenshots/).")

    # 12. Defensive Recommendations
    _h1(pdf, "12. Defensive Recommendations")
    recs = {d["recommended_action"] for d in data["detections"]}
    if recs:
        for r in sorted(recs):
            _p(pdf, f"- {r}")
    else:
        _p(pdf, "- Maintain baseline monitoring; no suspicious behaviour was detected.")

    # 13. Limitations
    _h1(pdf, "13. Limitations")
    _p(pdf, "Threat behaviour is synthetic; read-only observation reflects only what /proc "
            "exposes to the running user. The framework is single-host and demonstrates "
            "detection logic and workflow, not real malware capture.")

    # 14. Future Scope
    _h1(pdf, "14. Future Scope")
    _p(pdf, "Consented endpoint-agent telemetry, ML-based anomaly detection alongside the "
            "rule engine, SIEM export, and longitudinal behavioural baselining.")

    # 15. Conclusion
    _h1(pdf, "15. Conclusion")
    _p(pdf, f"In {session.get('mode','?')}, the lab produced a risk score of "
            f"{risk.get('score',0)} ({risk.get('level','LOW')}), demonstrating a transparent, "
            "reproducible defensive pipeline for studying keylogging behaviour safely.")

    pdf.output(str(out_path))
    return out_path


def _build_markdown(data: dict, out_path: Path) -> Path:
    """Fallback report if fpdf2 is unavailable."""
    summary = data["summary"]
    risk = summary.get("risk", {})
    lines = [f"# {__title__} — Experiment Report", ""]
    for i, section in enumerate(_SECTIONS, 1):
        lines.append(f"## {i}. {section}")
        lines.append("")
    lines.append(f"Risk: {risk.get('score', 0)} ({risk.get('level', 'LOW')})")
    out_path.write_text("\n".join(lines))
    return out_path


def generate_report(ctx: LabContext, store: Storage, session_id: int, summary: dict) -> Path:
    """Generate a PDF (or Markdown fallback) report for a session."""
    data = _gather(ctx, store, session_id, summary)
    ctx.paths.reports.mkdir(parents=True, exist_ok=True)
    if _HAS_FPDF:
        out = ctx.paths.reports / f"session_{session_id}_report.pdf"
        path = _build_pdf(data, ctx, out)
    else:
        out = ctx.paths.reports / f"session_{session_id}_report.md"
        path = _build_markdown(data, out)
        log.warning("fpdf2 not installed — wrote Markdown report instead of PDF.")
    log.info("Report written to %s", path)
    return path
