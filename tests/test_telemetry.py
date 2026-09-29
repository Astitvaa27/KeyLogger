"""Tests for Module 2 (telemetry) and Module 10 (modes)."""
from __future__ import annotations

from klab.config import ExperimentMode
from klab.modes import all_profiles, get_profile
from klab.telemetry import NAMED_DATASETS, generate_batch


def test_event_shape_and_source():
    events = generate_batch(ExperimentMode.NORMAL, 5, seed=1)
    assert len(events) == 5
    e = events[0]
    for key in (
        "timestamp", "process_name", "event_type", "event_count",
        "key_category", "duration_ms", "source",
        "persistence_indicator", "network_indicator", "event_rate_per_min",
    ):
        assert key in e
    assert e["source"] == "SIMULATED"
    assert e["event_type"] == "KEYBOARD_ACTIVITY"


def test_seed_is_reproducible():
    a = generate_batch(ExperimentMode.HIGH_RISK, 10, seed=99)
    b = generate_batch(ExperimentMode.HIGH_RISK, 10, seed=99)
    assert [x["event_count"] for x in a] == [x["event_count"] for x in b]


def test_zero_count_rejected():
    import pytest

    with pytest.raises(ValueError):
        generate_batch(ExperimentMode.NORMAL, 0)


def test_mode_profiles_present():
    profiles = {p.mode for p in all_profiles()}
    assert profiles == set(ExperimentMode)
    assert get_profile(ExperimentMode.HIGH_RISK).persistence_prob >= 0.8


def test_named_datasets_generate():
    for name, fn in NAMED_DATASETS.items():
        rows = fn(count=5, seed=3)
        assert len(rows) == 5, name


def test_high_volume_dataset_has_high_counts():
    rows = NAMED_DATASETS["high_volume_monitoring"](count=10, seed=3)
    assert all(r["event_count"] >= 2000 for r in rows)


def test_persistence_dataset_flags_all():
    rows = NAMED_DATASETS["suspicious_persistence"](count=10, seed=3)
    assert all(r["persistence_indicator"] for r in rows)
