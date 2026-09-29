"""Module 1 — Test Environment.

Collects read-only information about the Linux host the lab runs on: OS/kernel,
distribution, Python runtime, hostname/user, CPU/memory, uptime, and a snapshot
of processes that are relevant to the lab.

This module reads only public, non-sensitive system metadata. It does NOT read
user input, keystrokes, file contents, or credentials.
"""
from __future__ import annotations

import os
import platform
import socket
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from klab.logging_setup import get_logger

log = get_logger("environment")

# Process names considered "relevant to the lab" for display. Matched against
# the process NAME (comm) and executable basename only — NOT the full command
# line — so the repository path (which contains "KeyLogger") is not mistaken for
# a lab process. In practice no real process carries these names; the synthetic
# demo processes exist only as generated telemetry, so an empty result here is
# the expected, honest state on a clean host.
_LAB_KEYWORDS = ("keylog", "klab", "input-monitor", "demo-keylogger")


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cmdline: str
    lab_relevant: bool = False


@dataclass
class EnvironmentInfo:
    hostname: str
    os_system: str
    os_release: str
    kernel_version: str
    distribution: str
    architecture: str
    python_version: str
    python_executable: str
    username: str
    cpu_count: int
    total_memory_mb: float
    uptime_seconds: float
    is_linux: bool
    collected_at: str
    processes: list[ProcessInfo] = field(default_factory=list)

    @property
    def lab_processes(self) -> list[ProcessInfo]:
        return [p for p in self.processes if p.lab_relevant]


def _read_distribution() -> str:
    """Parse /etc/os-release for a human-friendly distribution name."""
    os_release = Path("/etc/os-release")
    if os_release.exists():
        try:
            data = {}
            for line in os_release.read_text().splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    data[k] = v.strip().strip('"')
            return data.get("PRETTY_NAME") or data.get("NAME") or "Unknown Linux"
        except OSError:
            pass
    return platform.platform()


def _read_total_memory_mb() -> float:
    """Read total RAM from /proc/meminfo (KB) -> MB. 0.0 if unavailable."""
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        try:
            for line in meminfo.read_text().splitlines():
                if line.startswith("MemTotal:"):
                    kb = float(line.split()[1])
                    return round(kb / 1024.0, 1)
        except (OSError, ValueError, IndexError):
            pass
    return 0.0


def _read_uptime_seconds() -> float:
    uptime = Path("/proc/uptime")
    if uptime.exists():
        try:
            return round(float(uptime.read_text().split()[0]), 1)
        except (OSError, ValueError, IndexError):
            pass
    return 0.0


def _iter_proc_pids():
    proc = Path("/proc")
    if not proc.exists():
        return
    for entry in proc.iterdir():
        if entry.name.isdigit():
            yield int(entry.name)


def list_processes(limit: int | None = None) -> list[ProcessInfo]:
    """Return a snapshot of running processes (name + cmdline) from /proc.

    Read-only. On non-Linux hosts (no /proc) this returns an empty list.
    """
    processes: list[ProcessInfo] = []
    for pid in _iter_proc_pids():
        base = Path(f"/proc/{pid}")
        try:
            name = (base / "comm").read_text().strip()
        except OSError:
            continue
        try:
            raw = (base / "cmdline").read_bytes()
            cmdline = raw.replace(b"\x00", b" ").decode(errors="replace").strip()
        except OSError:
            cmdline = ""
        # Relevance is decided by the process name and the executable's basename
        # only, never the full path, to avoid matching the repository directory.
        exe_basename = os.path.basename(cmdline.split(" ", 1)[0]) if cmdline else ""
        name_haystack = f"{name} {exe_basename}".lower()
        relevant = any(k in name_haystack for k in _LAB_KEYWORDS)
        processes.append(
            ProcessInfo(pid=pid, name=name, cmdline=cmdline, lab_relevant=relevant)
        )
        if limit and len(processes) >= limit:
            break
    return processes


def collect_environment(include_processes: bool = True) -> EnvironmentInfo:
    """Collect a full read-only snapshot of the lab environment."""
    uname = platform.uname()
    try:
        username = os.getlogin()
    except OSError:
        username = os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown"

    processes = list_processes() if include_processes else []
    info = EnvironmentInfo(
        hostname=socket.gethostname(),
        os_system=uname.system,
        os_release=uname.release,
        kernel_version=uname.version,
        distribution=_read_distribution(),
        architecture=platform.machine(),
        python_version=platform.python_version(),
        python_executable=sys.executable,
        username=username,
        cpu_count=os.cpu_count() or 0,
        total_memory_mb=_read_total_memory_mb(),
        uptime_seconds=_read_uptime_seconds(),
        is_linux=uname.system.lower() == "linux",
        collected_at=datetime.now(timezone.utc).isoformat(),
        processes=processes,
    )
    log.debug(
        "Collected environment: host=%s distro=%s procs=%d lab_procs=%d",
        info.hostname,
        info.distribution,
        len(info.processes),
        len(info.lab_processes),
    )
    return info
