"""Keystroke analytics service.

Computes behavioral statistics from stored keystroke *metadata*. No literal
characters are ever involved — only categories and timing.
"""
from __future__ import annotations

from statistics import median

from app.models.enums import KeyCategory
from app.models.keystroke import KeystrokeTestEvent
from app.schemas.keystroke import CategoryCount, KeystrokeStatistics

# Average characters per "word" used to derive a WPM figure from raw keystrokes.
_CHARS_PER_WORD = 5.0
# Intervals longer than this are treated as a deliberate pause, not typing.
_PAUSE_THRESHOLD_MS = 2000.0


def compute_statistics(
    session_id: int, events: list[KeystrokeTestEvent]
) -> KeystrokeStatistics:
    """Compute the full statistics bundle for a session's keystroke events."""
    total = len(events)

    intervals = [e.interval_ms for e in events if e.interval_ms and e.interval_ms > 0]
    avg_interval = sum(intervals) / len(intervals) if intervals else 0.0
    med_interval = float(median(intervals)) if intervals else 0.0

    # Session duration derived from the sum of inter-key intervals (seconds).
    duration_seconds = sum(intervals) / 1000.0 if intervals else 0.0

    kpm = (total / duration_seconds * 60.0) if duration_seconds > 0 else 0.0
    wpm = kpm / _CHARS_PER_WORD

    total_pause = sum(i for i in intervals if i >= _PAUSE_THRESHOLD_MS)

    backspace_count = sum(
        1 for e in events if e.category == KeyCategory.EDITING_KEY
    )
    backspace_rate = (backspace_count / total) if total else 0.0

    modifier_count = sum(1 for e in events if e.category == KeyCategory.MODIFIER)
    modifier_frequency = (modifier_count / total) if total else 0.0

    # Category distribution across all defined categories (stable ordering).
    counts: dict[KeyCategory, int] = {cat: 0 for cat in KeyCategory}
    for e in events:
        counts[e.category] = counts.get(e.category, 0) + 1
    distribution = [
        CategoryCount(category=cat, count=n) for cat, n in counts.items() if n > 0
    ]

    return KeystrokeStatistics(
        session_id=session_id,
        total_keystrokes=total,
        duration_seconds=round(duration_seconds, 3),
        keystrokes_per_minute=round(kpm, 2),
        typing_speed_wpm=round(wpm, 2),
        average_interval_ms=round(avg_interval, 2),
        median_interval_ms=round(med_interval, 2),
        total_pause_ms=round(total_pause, 2),
        backspace_count=backspace_count,
        backspace_rate=round(backspace_rate, 4),
        modifier_count=modifier_count,
        modifier_frequency=round(modifier_frequency, 4),
        category_distribution=distribution,
    )
