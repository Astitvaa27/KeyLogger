"""Module 10 — Experiment modes.

Each mode is a profile that biases synthetic telemetry generation so the lab can
demonstrate how the defensive pipeline distinguishes ordinary activity from
suspicious keylogging-like behaviour. The profiles are pure data — they perform
no action themselves.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from klab.config import ExperimentMode


@dataclass(frozen=True)
class ModeProfile:
    """Parameters controlling synthetic telemetry for a mode."""

    mode: ExperimentMode
    description: str
    # keyboard event_count range per generated event
    event_count_range: tuple[int, int]
    # events-per-minute rate range
    rate_range: tuple[int, int]
    # probability a given event carries each indicator
    persistence_prob: float
    network_prob: float
    # candidate synthetic process names for this mode
    process_names: tuple[str, ...] = field(
        default=("user-app", "text-editor", "terminal")
    )
    # candidate key categories
    key_categories: tuple[str, ...] = field(
        default=("ALPHANUMERIC", "MODIFIER", "WHITESPACE", "NAVIGATION", "EDITING")
    )


_PROFILES: dict[ExperimentMode, ModeProfile] = {
    ExperimentMode.NORMAL: ModeProfile(
        mode=ExperimentMode.NORMAL,
        description="Ordinary human typing activity; low, human-scale volumes.",
        event_count_range=(5, 120),
        rate_range=(10, 60),
        persistence_prob=0.02,
        network_prob=0.03,
        process_names=("gedit", "code", "bash", "firefox", "libreoffice"),
    ),
    ExperimentMode.SUSPICIOUS: ModeProfile(
        mode=ExperimentMode.SUSPICIOUS,
        description="Mixed indicators; some events look like input monitoring.",
        event_count_range=(100, 900),
        rate_range=(60, 260),
        persistence_prob=0.45,
        network_prob=0.4,
        process_names=("input-monitor", "helper-daemon", "demo-keylogger", "sync-agent"),
    ),
    ExperimentMode.HIGH_RISK: ModeProfile(
        mode=ExperimentMode.HIGH_RISK,
        description="Strong keylogger-like signals: high volume, persistence, network.",
        event_count_range=(1200, 6000),
        rate_range=(300, 950),
        persistence_prob=0.9,
        network_prob=0.9,
        process_names=("demo-keylogger", "kbd-capture", "input-monitor", "exfil-agent"),
    ),
}


def get_profile(mode: ExperimentMode) -> ModeProfile:
    return _PROFILES[mode]


def all_profiles() -> list[ModeProfile]:
    return list(_PROFILES.values())
