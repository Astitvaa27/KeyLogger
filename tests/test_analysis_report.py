"""Tests for Module 8 (analysis/export) and Module 9 (report)."""
from __future__ import annotations

from klab import analysis as analysis_mod
from klab.config import ExperimentMode, build_context
from klab.detection import analyze
from klab.report import generate_report
from klab.risk import score
from klab.storage import Storage
from klab.telemetry import generate_batch


def _populate(store: Storage, mode: ExperimentMode) -> int:
    sid = store.create_session(mode.value)
    events = generate_batch(mode, 40, seed=4)
    store.add_events(sid, events)
    dets = analyze(events, [])
    store.add_detections(sid, [d.to_dict() for d in dets])
    r = score(dets)
    store.add_risk_score(sid, r.score, r.level, r.breakdown)
    store.end_session(sid, len(events))
    return sid


def test_analysis_summary_structure(tmp_path):
    with Storage(tmp_path / "a.sqlite3") as store:
        sid = _populate(store, ExperimentMode.HIGH_RISK)
        summary = analysis_mod.analyze_session(store, sid)
    assert summary["totals"]["events"] == 40
    assert summary["risk"]["level"] == "CRITICAL"
    assert summary["event_volume"]["max"] >= summary["event_volume"]["min"]
    assert "by_process" in summary["event_frequency"]


def test_exports_written(tmp_path):
    with Storage(tmp_path / "a.sqlite3") as store:
        sid = _populate(store, ExperimentMode.SUSPICIOUS)
        summary = analysis_mod.analyze_session(store, sid)
        paths = analysis_mod.export_all(store, summary, tmp_path / "datasets", sid)
    assert len(paths) == 3
    for p in paths:
        assert p.exists() and p.stat().st_size > 0
    assert any(p.suffix == ".json" for p in paths)
    assert sum(1 for p in paths if p.suffix == ".csv") == 2


def test_report_generation(tmp_path):
    ctx = build_context(base_dir=str(tmp_path))
    for d in ctx.paths.all_dirs():
        d.mkdir(parents=True, exist_ok=True)
    with Storage(ctx.paths.database) as store:
        sid = _populate(store, ExperimentMode.HIGH_RISK)
        summary = analysis_mod.analyze_session(store, sid)
        path = generate_report(ctx, store, sid, summary)
    assert path.exists()
    data = path.read_bytes()
    # Either a real PDF (fpdf2 present) or the Markdown fallback.
    assert data[:5] == b"%PDF-" or path.suffix == ".md"
    assert len(data) > 500
