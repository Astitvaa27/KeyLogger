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


def test_later_phase_commands_are_registered(tmp_path, capsys):
    for cmd in ("test", "analyze", "report"):
        rc = main(["--home", str(tmp_path), cmd])
        assert rc == 0
        out = capsys.readouterr().out
        assert cmd.upper() in out


def test_version_flag():
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
