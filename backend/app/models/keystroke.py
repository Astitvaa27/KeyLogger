"""Keystroke test event model.

IMPORTANT (safety): this table stores keystroke *metadata* only — the key
category, timing, and sequence — captured exclusively inside the in-app
Virtual Keylogger Lab while a test is explicitly active. The literal typed
character is NOT stored. A single optional `key_label` column exists only for
non-sensitive, whitelisted control keys (e.g. "Enter", "Shift") and is never
populated with alphanumeric input.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import KeyCategory

if TYPE_CHECKING:
    from app.models.session import Session


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KeystrokeTestEvent(Base):
    __tablename__ = "keystroke_test_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[KeyCategory] = mapped_column(SAEnum(KeyCategory), nullable=False)
    # Non-sensitive label for control keys only (e.g. "Enter"); never letters/digits.
    key_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Milliseconds since the previous event in this session (inter-key interval).
    interval_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Key hold duration in ms, when safely available (keydown -> keyup).
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_timestamp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    session: Mapped["Session"] = relationship(back_populates="keystroke_events")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KeystrokeTestEvent seq={self.sequence_number} cat={self.category}>"
