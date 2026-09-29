"""Keystroke ingestion and analytics routes.

Accepts keystroke *metadata* batches from the in-app Virtual Keylogger Lab and
returns computed behavioral statistics. Never accepts or stores literal typed
characters.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import SessionStatus
from app.models.keystroke import KeystrokeTestEvent
from app.models.session import Session
from app.models.user import User
from app.schemas.keystroke import (
    KeystrokeBatchIn,
    KeystrokeBatchResult,
    KeystrokeStatistics,
)
from app.services.analytics import compute_statistics

router = APIRouter(prefix="/keystrokes", tags=["keystrokes"])


def _get_owned_session(db: DBSession, session_id: int, user: User) -> Session:
    session = db.get(Session, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/events", response_model=KeystrokeBatchResult, status_code=status.HTTP_201_CREATED)
def ingest_events(
    payload: KeystrokeBatchIn,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingest a batch of keystroke metadata events for an active session."""
    session = _get_owned_session(db, payload.session_id, current_user)
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is not active; start a test before sending events.",
        )

    for ev in payload.events:
        db.add(
            KeystrokeTestEvent(
                session_id=session.id,
                sequence_number=ev.sequence_number,
                category=ev.category,
                key_label=ev.key_label,
                interval_ms=ev.interval_ms,
                duration_ms=ev.duration_ms,
                client_timestamp_ms=ev.client_timestamp_ms,
            )
        )
    session.total_keystrokes += len(payload.events)
    db.commit()

    return KeystrokeBatchResult(
        session_id=session.id,
        accepted=len(payload.events),
        total_in_session=session.total_keystrokes,
    )


@router.get("/statistics", response_model=KeystrokeStatistics)
def statistics(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute behavioral statistics for a session's keystroke metadata."""
    session = _get_owned_session(db, session_id, current_user)
    events = db.scalars(
        select(KeystrokeTestEvent)
        .where(KeystrokeTestEvent.session_id == session.id)
        .order_by(KeystrokeTestEvent.sequence_number.asc())
    ).all()
    return compute_statistics(session.id, list(events))
