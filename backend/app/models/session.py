"""Test session model.

A Session represents one explicitly user-initiated run of the Virtual
Keylogger Lab, the threat simulator, or a combined analysis session.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SessionStatus

if TYPE_CHECKING:
    from app.models.detection import DetectionResult
    from app.models.keystroke import KeystrokeTestEvent
    from app.models.simulation import SimulationEvent
    from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_keystrokes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")
    keystroke_events: Mapped[list["KeystrokeTestEvent"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    simulation_events: Mapped[list["SimulationEvent"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    detection_results: Mapped[list["DetectionResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Session id={self.id} status={self.status}>"
