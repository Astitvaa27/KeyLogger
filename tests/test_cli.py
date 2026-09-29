"""Tests for the CLI: setup/status dispatch and workspace initialization."""
from __future__ import annotations

from klab.cli import main


def test_setup_initializes_workspace(tmp_path, capsys):
    rc = main(["--home", str(tmp_path), "setup"])
    assert rc == 0
    # Setup must create the directory layout and config file.
    assert (tmp_path / "config.json").exists()
    assert (tmp_path / "logs").exists()
    assert (tmp_path / "datasets").exists()
    assert (tmp_path / "reports").exists()
    out = capsys.readouterr().out
    assert "SETUP" in out
    assert "Setup complete" in out


def test_status_reports_uninitialized_then_initialized(tmp_path, capsys):
    # Before setup.
    rc = main(["--home", str(tmp_path), "status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "NO" in out  # not initialized

    # After setup.
    main(["--home", str(tmp_path), "setup"])
    capsys.readouterr()  # clear
    rc = main(["--home", str(tmp_path), "status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Configuration" in out
    assert "Linux Environment" in out


def test_invalid_mode_is_rejected(tmp_path):
    # argparse .error raises SystemExit(2).
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["--home", str(tmp_path), "--mode", "nonsense", "status"])
    assert exc.value.code == 2


def test_end_to_end_flow(tmp_path, capsys):
    # setup -> test -> analyze -> report, all succeeding and producing artifacts.
    assert main(["--home", str(tmp_path), "setup"]) == 0
    capsys.readouterr()

    rc = main(["--home", str(tmp_path), "--mode", "HIGH_RISK", "test",
               "--count", "30", "--seed", "1", "--no-monitor"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Risk score" in out and "CRITICAL" in out

    assert main(["--home", str(tmp_path), "analyze"]) == 0
    out = capsys.readouterr().out
    assert "analysis" in out.lower()
    assert (tmp_path / "datasets").exists()
    assert any((tmp_path / "datasets").glob("*.json"))

    assert main(["--home", str(tmp_path), "report"]) == 0
    out = capsys.readouterr().out
    assert "report generated" in out.lower()
    assert any((tmp_path / "reports").glob("session_*_report.*"))


def test_analyze_without_data_returns_1(tmp_path):
    # No test run yet -> analyze should fail gracefully.
    assert main(["--home", str(tmp_path), "analyze"]) == 1


def test_normal_mode_is_low_risk(tmp_path, capsys):
    main(["--home", str(tmp_path), "setup"])
    capsys.readouterr()
    main(["--home", str(tmp_path), "--mode", "NORMAL", "test",
          "--count", "50", "--seed", "1", "--no-monitor"])
    out = capsys.readouterr().out
    assert "LOW" in out


def test_version_flag():
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
