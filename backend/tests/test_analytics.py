"""Unit tests for the keystroke analytics service."""
from __future__ import annotations

from app.models.enums import KeyCategory
from app.models.keystroke import KeystrokeTestEvent
from app.services.analytics import compute_statistics


def _event(seq, category, interval=None):
    return KeystrokeTestEvent(
        session_id=1,
        sequence_number=seq,
        category=category,
        interval_ms=interval,
    )


def test_empty_session_stats_are_zero():
    stats = compute_statistics(1, [])
    assert stats.total_keystrokes == 0
    assert stats.keystrokes_per_minute == 0
    assert stats.average_interval_ms == 0
    assert stats.category_distribution == []


def test_basic_statistics():
    events = [
        _event(0, KeyCategory.LETTER, None),
        _event(1, KeyCategory.LETTER, 100),
        _event(2, KeyCategory.LETTER, 200),
        _event(3, KeyCategory.EDITING_KEY, 300),
        _event(4, KeyCategory.MODIFIER, 100),
    ]
    stats = compute_statistics(1, events)
    assert stats.total_keystrokes == 5
    # Intervals: 100,200,300,100 -> avg 175, median 150
    assert stats.average_interval_ms == 175.0
    assert stats.median_interval_ms == 150.0
    assert stats.backspace_count == 1
    assert stats.backspace_rate == 0.2
    assert stats.modifier_count == 1
    # duration = (100+200+300+100)/1000 = 0.7s
    assert stats.duration_seconds == 0.7


def test_category_distribution_counts():
    events = [
        _event(0, KeyCategory.LETTER),
        _event(1, KeyCategory.LETTER),
        _event(2, KeyCategory.DIGIT),
    ]
    stats = compute_statistics(1, events)
    dist = {c.category: c.count for c in stats.category_distribution}
    assert dist[KeyCategory.LETTER] == 2
    assert dist[KeyCategory.DIGIT] == 1
    assert KeyCategory.MODIFIER not in dist  # zero-count categories omitted
