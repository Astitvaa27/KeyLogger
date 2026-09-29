"""Keystroke event & analytics schemas.

The API accepts only key *category* metadata and timing — never the literal
typed characters. `key_label` is optional and intended only for non-sensitive
control keys (validated server-side).
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.models.enums import KeyCategory

# Control keys that may safely be labeled; anything else is dropped.
_ALLOWED_LABELS = {
    "Enter",
    "Shift",
    "Control",
    "Alt",
    "Meta",
    "Tab",
    "Backspace",
    "Delete",
    "CapsLock",
    "Escape",
    "ArrowUp",
    "ArrowDown",
    "ArrowLeft",
    "ArrowRight",
    "Home",
    "End",
    "PageUp",
    "PageDown",
    "Space",
}


class KeystrokeEventIn(BaseModel):
    sequence_number: int = Field(ge=0)
    category: KeyCategory
    key_label: str | None = Field(default=None, max_length=32)
    interval_ms: float | None = Field(default=None, ge=0)
    duration_ms: float | None = Field(default=None, ge=0)
    client_timestamp_ms: float | None = Field(default=None, ge=0)

    @field_validator("key_label")
    @classmethod
    def _sanitize_label(cls, value: str | None) -> str | None:
        # Only whitelisted, non-sensitive control-key labels are retained.
        if value is None:
            return None
        return value if value in _ALLOWED_LABELS else None


class KeystrokeBatchIn(BaseModel):
    session_id: int
    events: list[KeystrokeEventIn] = Field(min_length=1, max_length=5000)


class KeystrokeBatchResult(BaseModel):
    session_id: int
    accepted: int
    total_in_session: int


class CategoryCount(BaseModel):
    category: KeyCategory
    count: int


class KeystrokeStatistics(BaseModel):
    session_id: int
    total_keystrokes: int
    duration_seconds: float
    keystrokes_per_minute: float
    typing_speed_wpm: float
    average_interval_ms: float
    median_interval_ms: float
    total_pause_ms: float
    backspace_count: int
    backspace_rate: float
    modifier_count: int
    modifier_frequency: float
    category_distribution: list[CategoryCount]
