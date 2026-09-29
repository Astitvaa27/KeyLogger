"""Configuration, filesystem paths, and shared constants for the lab.

Configuration is intentionally simple and file-based (JSON) so it is easy to
inspect and reproduce inside a VM. Nothing here reads secrets or credentials.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path


class ExperimentMode(str, Enum):
    """Experiment modes that bias synthetic telemetry generation (Module 10)."""

    NORMAL = "NORMAL_MODE"
    SUSPICIOUS = "SUSPICIOUS_MODE"
    HIGH_RISK = "HIGH_RISK_MODE"

    @classmethod
    def from_str(cls, value: str) -> "ExperimentMode":
        value = (value or "").strip().upper()
        # Accept short aliases: NORMAL, SUSPICIOUS, HIGH_RISK / HIGH.
        aliases = {
            "NORMAL": cls.NORMAL,
            "NORMAL_MODE": cls.NORMAL,
            "SUSPICIOUS": cls.SUSPICIOUS,
            "SUSPICIOUS_MODE": cls.SUSPICIOUS,
            "HIGH": cls.HIGH_RISK,
            "HIGH_RISK": cls.HIGH_RISK,
            "HIGH_RISK_MODE": cls.HIGH_RISK,
        }
        if value not in aliases:
            raise ValueError(
                f"Unknown experiment mode: {value!r}. "
                f"Choose NORMAL, SUSPICIOUS, or HIGH_RISK."
            )
        return aliases[value]


# ---------------------------------------------------------------------------
# Filesystem layout. Everything the lab writes lives under a single base dir so
# the experiment is self-contained and easy to inspect or wipe.
# ---------------------------------------------------------------------------
def _default_base_dir() -> Path:
    # Allow override via env for CI/tests; default to <repo>/data.
    env = os.environ.get("KLAB_HOME")
    if env:
        return Path(env).expanduser().resolve()
    # config.py -> src/klab/config.py ; repo root is three parents up.
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data"


@dataclass
class Paths:
    base: Path

    @property
    def config_file(self) -> Path:
        return self.base / "config.json"

    @property
    def database(self) -> Path:
        return self.base / "klab.sqlite3"

    @property
    def logs(self) -> Path:
        return self.base / "logs"

    @property
    def datasets(self) -> Path:
        return self.base / "datasets"

    @property
    def reports(self) -> Path:
        return self.base / "reports"

    def all_dirs(self) -> list[Path]:
        return [self.base, self.logs, self.datasets, self.reports]


@dataclass
class Config:
    """Serializable lab configuration."""

    lab_name: str = "Linux Keylogging Defense Lab"
    default_mode: str = ExperimentMode.NORMAL.value
    log_level: str = "INFO"
    # Number of synthetic telemetry events a single `test` run generates.
    default_event_batch: int = 50
    # Authorization acknowledgement — the operator confirms this is their own VM.
    authorized_lab: bool = True
    schema_version: int = 1

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_file(cls, path: Path) -> "Config":
        data = json.loads(path.read_text())
        known = {f for f in cls().__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class LabContext:
    """Bundle passed to command handlers: resolved paths + loaded config."""

    paths: Paths
    config: Config
    mode: ExperimentMode = ExperimentMode.NORMAL

    @property
    def is_initialized(self) -> bool:
        return self.paths.config_file.exists() and self.paths.database.exists()


def build_context(
    base_dir: str | os.PathLike | None = None,
    mode: str | None = None,
) -> LabContext:
    """Construct a LabContext, loading config from disk if present."""
    base = Path(base_dir).expanduser().resolve() if base_dir else _default_base_dir()
    paths = Paths(base=base)
    config = Config.from_file(paths.config_file) if paths.config_file.exists() else Config()
    resolved_mode = (
        ExperimentMode.from_str(mode) if mode else ExperimentMode.from_str(config.default_mode)
    )
    return LabContext(paths=paths, config=config, mode=resolved_mode)


# Detection / scoring thresholds shared across modules (kept here so tuning is
# centralized and transparent).
THRESHOLDS = {
    "high_keyboard_event_volume": 1000,   # events per observation window
    "abnormal_event_rate_per_min": 300,   # events/min considered non-human
    "high_cpu_percent": 80.0,
    "high_memory_mb": 500.0,
}
