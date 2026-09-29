"""Tests for configuration and lab context."""
from __future__ import annotations

import pytest

from klab.config import Config, ExperimentMode, build_context


def test_experiment_mode_aliases():
    assert ExperimentMode.from_str("normal") is ExperimentMode.NORMAL
    assert ExperimentMode.from_str("SUSPICIOUS_MODE") is ExperimentMode.SUSPICIOUS
    assert ExperimentMode.from_str("high") is ExperimentMode.HIGH_RISK
    assert ExperimentMode.from_str("HIGH_RISK") is ExperimentMode.HIGH_RISK


def test_experiment_mode_invalid():
    with pytest.raises(ValueError):
        ExperimentMode.from_str("banana")


def test_config_json_roundtrip(tmp_path):
    cfg = Config(log_level="DEBUG", default_event_batch=99)
    path = tmp_path / "config.json"
    path.write_text(cfg.to_json())
    loaded = Config.from_file(path)
    assert loaded.log_level == "DEBUG"
    assert loaded.default_event_batch == 99


def test_build_context_uses_home(tmp_path):
    ctx = build_context(base_dir=str(tmp_path), mode="SUSPICIOUS")
    assert ctx.paths.base == tmp_path.resolve()
    assert ctx.mode is ExperimentMode.SUSPICIOUS
    assert not ctx.is_initialized  # nothing created yet
    assert ctx.paths.database == tmp_path.resolve() / "klab.sqlite3"


def test_config_from_file_ignores_unknown_keys(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"lab_name": "X", "unknown_field": 1}')
    cfg = Config.from_file(path)
    assert cfg.lab_name == "X"
