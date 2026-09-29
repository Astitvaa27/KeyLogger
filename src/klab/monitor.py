"""Module 3 — Linux behaviour monitor (read-only).

Produces read-only metadata about running processes: PID, name, parent PID,
CPU%, memory, executable path, command line, and a coarse network-activity
indicator. It uses ``psutil`` when available and falls back to reading ``/proc``
directly.

SAFETY: This module only *reads* public process metadata. It never captures
user input, attaches to processes, or inspects process memory/keystrokes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from klab.logging_setup import get_logger

log = get_logger("monitor")

try:  # optional dependency
    import psutil  # type: ignore

    _HAS_PSUTIL = True
except Exception:  # pragma: no cover - environment dependent
    psutil = None  # type: ignore
    _HAS_PSUTIL = False

# Process-name substrings that the monitor treats as noteworthy for the lab.
_WATCH_NAMES = ("keylog", "kbd-capture", "input-monitor", "demo-keylogger", "exfil")


@dataclass
class ProcessObservation:
    pid: int
    name: str
    ppid: int | None = None
    cpu_percent: float | None = None
    memory_mb: float | None = None
    exe_path: str | None = None
    cmdline: str | None = None
    network_activity: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def noteworthy(self) -> bool:
        base = (self.name or "").lower()
        exe = Path(self.exe_path or "").name.lower()
        return any(k in base or k in exe for k in _WATCH_NAMES)

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# psutil backend
# --------------------------------------------------------------------------
def _observe_psutil() -> list[ProcessObservation]:
    observations: list[ProcessObservation] = []
    # Prime cpu_percent (first call returns 0.0 for every process).
    for proc in psutil.process_iter():  # type: ignore[union-attr]
        try:
            proc.cpu_percent(None)
        except Exception:
            continue

    conns_by_pid: dict[int, bool] = {}
    try:
        for c in psutil.net_connections(kind="inet"):  # type: ignore[union-attr]
            if c.pid:
                conns_by_pid[c.pid] = True
    except Exception:
        # net_connections may require privileges; degrade gracefully.
        conns_by_pid = {}

    for proc in psutil.process_iter(
        ["pid", "name", "ppid", "memory_info", "exe", "cmdline"]
    ):  # type: ignore[union-attr]
        try:
            info = proc.info
            mem = info.get("memory_info")
            memory_mb = round(mem.rss / (1024 * 1024), 2) if mem else None
            cmdline = " ".join(info.get("cmdline") or []) or None
            observations.append(
                ProcessObservation(
                    pid=info["pid"],
                    name=info.get("name") or "",
                    ppid=info.get("ppid"),
                    cpu_percent=round(proc.cpu_percent(None), 2),
                    memory_mb=memory_mb,
                    exe_path=info.get("exe"),
                    cmdline=cmdline,
                    network_activity=conns_by_pid.get(info["pid"], False),
                )
            )
        except Exception:
            continue
    return observations


# --------------------------------------------------------------------------
# /proc fallback backend
# --------------------------------------------------------------------------
def _read_first(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def _observe_proc() -> list[ProcessObservation]:
    proc_root = Path("/proc")
    if not proc_root.exists():
        return []
    page_size = 4096
    observations: list[ProcessObservation] = []
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        name = _read_first(entry / "comm") or ""
        ppid = None
        stat = _read_first(entry / "stat")
        if stat:
            # After the (comm) field, field 2 (0-indexed 1 after ')') is ppid.
            try:
                after = stat.rsplit(")", 1)[1].split()
                ppid = int(after[1])
            except (IndexError, ValueError):
                ppid = None
        memory_mb = None
        statm = _read_first(entry / "statm")
        if statm:
            try:
                rss_pages = int(statm.split()[1])
                memory_mb = round(rss_pages * page_size / (1024 * 1024), 2)
            except (IndexError, ValueError):
                memory_mb = None
        try:
            raw = (entry / "cmdline").read_bytes()
            cmdline = raw.replace(b"\x00", b" ").decode(errors="replace").strip() or None
        except OSError:
            cmdline = None
        exe_path = None
        try:
            exe_path = str((entry / "exe").resolve())
        except OSError:
            exe_path = None
        observations.append(
            ProcessObservation(
                pid=pid,
                name=name,
                ppid=ppid,
                cpu_percent=None,  # not sampled in the lightweight fallback
                memory_mb=memory_mb,
                exe_path=exe_path,
                cmdline=cmdline,
                network_activity=False,
            )
        )
    return observations


def observe_processes() -> list[ProcessObservation]:
    """Return a read-only snapshot of running processes."""
    obs = _observe_psutil() if _HAS_PSUTIL else _observe_proc()
    log.info(
        "Observed %d processes via %s backend",
        len(obs),
        "psutil" if _HAS_PSUTIL else "/proc",
    )
    return obs


def backend_name() -> str:
    return "psutil" if _HAS_PSUTIL else "/proc"
