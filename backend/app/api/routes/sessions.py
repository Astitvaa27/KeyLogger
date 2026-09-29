"""Session lifecycle routes: start, stop, list, get."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user, get_owned_session
from app.core.database import get_db
from app.models.enums import SessionStatus
from app.models.session import Session
from app.models.user import User
from app.schemas.session import SessionCreate, SessionOut
from app.services import audit

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Explicitly start a new test session (required before any capture)."""
    session = Session(
        user_id=current_user.id,
        label=payload.label,
        status=SessionStatus.ACTIVE,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    audit.record(
        db, user_id=current_user.id, action="session.start", detail=f"session_id={session.id}"
    )
    return session


@router.post("/stop", response_model=SessionOut)
def stop_session(
    session: Session = Depends(get_owned_session),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop an active session (query param: session_id)."""
    if session.status == SessionStatus.ACTIVE:
        session.status = SessionStatus.STOPPED
        session.ended_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        audit.record(
            db,
            user_id=current_user.id,
            action="session.stop",
            detail=f"session_id={session.id}",
        )
    return session


@router.get("", response_model=list[SessionOut])
def list_sessions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's sessions, newest first."""
    rows = db.scalars(
        select(Session)
        .where(Session.user_id == current_user.id)
        .order_by(Session.started_at.desc())
    ).all()
    return rows


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session: Session = Depends(get_owned_session)):
    """Fetch a single owned session."""
    return session
