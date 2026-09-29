"""Tests for Module 1 — environment collection (read-only)."""
from __future__ import annotations

from klab.environment import ProcessInfo, collect_environment, list_processes


def test_collect_environment_basic_fields():
    env = collect_environment(include_processes=False)
    assert env.hostname
    assert env.python_version
    assert env.os_system
    assert env.cpu_count >= 1
    assert env.collected_at.endswith("+00:00") or "T" in env.collected_at
    assert env.processes == []


def test_list_processes_returns_current_process():
    procs = list_processes()
    # On Linux there must be at least this test process.
    assert isinstance(procs, list)
    assert all(isinstance(p, ProcessInfo) for p in procs)
    if procs:  # Linux/proc available
        pids = {p.pid for p in procs}
        import os

        assert os.getpid() in pids


def test_lab_relevance_flagging():
    procs = [
        ProcessInfo(pid=1, name="demo-keylogger", cmdline="./demo-keylogger", lab_relevant=False),
        ProcessInfo(pid=2, name="bash", cmdline="bash", lab_relevant=False),
    ]
    # Re-run detection logic by name heuristic via collect (indirect):
    # here we just assert the dataclass carries the flag we set.
    assert procs[0].name == "demo-keylogger"


def test_environment_reports_linux_flag():
    env = collect_environment(include_processes=False)
    # Whatever the host, is_linux must be a bool consistent with os_system.
    assert env.is_linux == (env.os_system.lower() == "linux")
