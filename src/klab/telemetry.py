"""Module 2 — Synthetic keystroke telemetry.

Generates SAFE, fabricated telemetry describing hypothetical keyboard activity.
No real keys, characters, or credentials are ever recorded. Every event is
tagged ``source="SIMULATED"``.

An event dict looks like:

    {
        "timestamp": "2026-...Z",
        "process_name": "demo-keylogger",
        "event_type": "KEYBOARD_ACTIVITY",
        "event_count": 143,
        "key_category": "ALPHANUMERIC",
        "duration_ms": 1820.0,
        "source": "SIMULATED",
        "persistence_indicator": true,
        "network_indicator": true,
        "event_rate_per_min": 420
    }
"""
from __future__ import annotations

import random
from datetime import datetime, timezone

from klab.config import ExperimentMode
from klab.logging_setup import get_logger
from klab.modes import ModeProfile, get_profile

log = get_logger("telemetry")

EVENT_TYPE = "KEYBOARD_ACTIVITY"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_event(profile: ModeProfile, rng: random.Random) -> dict:
    """Generate a single synthetic telemetry event from a mode profile."""
    event_count = rng.randint(*profile.event_count_range)
    rate = rng.randint(*profile.rate_range)
    persistence = rng.random() < profile.persistence_prob
    network = rng.random() < profile.network_prob
    return {
        "timestamp": _now_iso(),
        "process_name": rng.choice(profile.process_names),
        "event_type": EVENT_TYPE,
        "event_count": event_count,
        "key_category": rng.choice(profile.key_categories),
        "duration_ms": round(rng.uniform(50.0, 5000.0), 1),
        "source": "SIMULATED",
        "persistence_indicator": persistence,
        "network_indicator": network,
        "event_rate_per_min": rate,
    }


def generate_batch(
    mode: ExperimentMode, count: int, seed: int | None = None
) -> list[dict]:
    """Generate a batch of synthetic events for a mode.

    A fixed ``seed`` makes the batch reproducible (useful for experiments/tests).
    """
    if count < 1:
        raise ValueError("count must be >= 1")
    profile = get_profile(mode)
    rng = random.Random(seed)
    events = [generate_event(profile, rng) for _ in range(count)]
    log.info("Generated %d synthetic events (mode=%s, seed=%s)", count, mode.value, seed)
    return events


# ---- Named reference datasets (Module 2 requirement) ---------------------
def dataset_normal_activity(count: int = 50, seed: int | None = None) -> list[dict]:
    return generate_batch(ExperimentMode.NORMAL, count, seed)


def dataset_suspicious_activity(count: int = 50, seed: int | None = None) -> list[dict]:
    return generate_batch(ExperimentMode.SUSPICIOUS, count, seed)


def dataset_high_volume_monitoring(count: int = 30, seed: int | None = None) -> list[dict]:
    """High-volume keyboard-monitoring dataset (all events high event_count)."""
    profile = get_profile(ExperimentMode.HIGH_RISK)
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        e = generate_event(profile, rng)
        e["event_count"] = rng.randint(2000, 8000)
        e["event_rate_per_min"] = rng.randint(500, 1200)
        out.append(e)
    return out


def dataset_suspicious_persistence(count: int = 30, seed: int | None = None) -> list[dict]:
    """Persistence-heavy dataset (every event carries the persistence flag)."""
    profile = get_profile(ExperimentMode.SUSPICIOUS)
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        e = generate_event(profile, rng)
        e["persistence_indicator"] = True
        out.append(e)
    return out


def dataset_suspicious_network(count: int = 30, seed: int | None = None) -> list[dict]:
    """Network-communication dataset (every event carries the network flag)."""
    profile = get_profile(ExperimentMode.SUSPICIOUS)
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        e = generate_event(profile, rng)
        e["network_indicator"] = True
        out.append(e)
    return out


NAMED_DATASETS = {
    "normal_activity": dataset_normal_activity,
    "suspicious_activity": dataset_suspicious_activity,
    "high_volume_monitoring": dataset_high_volume_monitoring,
    "suspicious_persistence": dataset_suspicious_persistence,
    "suspicious_network": dataset_suspicious_network,
}
