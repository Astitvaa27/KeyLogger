"""Synthetic threat simulation service.

Generates FABRICATED telemetry describing a hypothetical keylogging process.
Nothing here touches the real OS, real processes, or the network. It exists
only to feed the defensive detection engine with realistic-looking test data.
"""
from __future__ import annotations

import random

# Fabricated process names for the hypothetical (fake) suspicious process.
_DEMO_PROCESS_NAMES = [
    "demo-keylogger.exe",
    "sim-input-monitor.exe",
    "test-capture-agent.exe",
    "synthetic-logger.bin",
    "labdemo-hook.exe",
]

# Profiles bias the random telemetry toward benign or suspicious values.
_PROFILES = {
    "benign": {
        "kb_range": (10, 200),
        "rate_range": (5, 40),
        "persistence_prob": 0.05,
        "network_prob": 0.05,
    },
    "balanced": {
        "kb_range": (200, 1500),
        "rate_range": (40, 250),
        "persistence_prob": 0.5,
        "network_prob": 0.5,
    },
    "aggressive": {
        "kb_range": (1500, 6000),
        "rate_range": (250, 900),
        "persistence_prob": 0.9,
        "network_prob": 0.9,
    },
}

# Thresholds used both here (to tag indicators) and by the detection engine.
HIGH_KEYBOARD_VOLUME = 1000
ABNORMAL_EVENT_RATE = 300


def _derive_indicators(
    keyboard_events: int,
    persistence: bool,
    network: bool,
    event_rate: int,
) -> list[str]:
    """Tag which risk indicators this synthetic event exhibits."""
    indicators: list[str] = []
    if keyboard_events >= HIGH_KEYBOARD_VOLUME:
        indicators.append("high_keyboard_event_volume")
    if persistence:
        indicators.append("persistence_indicator")
    if network:
        indicators.append("network_communication")
    if event_rate >= ABNORMAL_EVENT_RATE:
        indicators.append("abnormal_event_frequency")
    # Suspicious process behavior: co-occurrence of persistence AND network.
    if persistence and network:
        indicators.append("suspicious_process_behavior")
    return indicators


def generate_event(profile: str = "balanced") -> dict:
    """Generate a single synthetic telemetry event as a plain dict."""
    cfg = _PROFILES.get(profile, _PROFILES["balanced"])
    keyboard_events = random.randint(*cfg["kb_range"])
    event_rate = random.randint(*cfg["rate_range"])
    persistence = random.random() < cfg["persistence_prob"]
    network = random.random() < cfg["network_prob"]

    indicators = _derive_indicators(keyboard_events, persistence, network, event_rate)

    return {
        "process_name": random.choice(_DEMO_PROCESS_NAMES),
        "keyboard_events": keyboard_events,
        "persistence_indicator": persistence,
        "network_activity": network,
        "event_rate_per_min": event_rate,
        "risk_indicators": indicators,
    }


def generate_events(count: int, profile: str = "balanced") -> list[dict]:
    """Generate a batch of synthetic telemetry events."""
    return [generate_event(profile) for _ in range(count)]
