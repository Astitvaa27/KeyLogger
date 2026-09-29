"""Synthetic threat simulation routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.session import Session
from app.models.simulation import SimulationEvent
from app.models.user import User
from app.schemas.simulation import (
    SimulationEventOut,
    SimulationGenerateIn,
    SimulationStartIn,
)
from app.services import audit, simulation as sim_service

router = APIRouter(prefix="/simulation", tags=["simulation"])

# In-memory simulation run state per session (safe: process-local, non-persistent).
_running: dict[int, str] = {}


def _get_owned_session(db: DBSession, session_id: int, user: User) -> Session:
    session = db.get(Session, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _persist(db: DBSession, session_id: int, events: list[dict]) -> list[SimulationEvent]:
    rows = [SimulationEvent(session_id=session_id, **e) for e in events]
    db.add_all(rows)
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows


@router.post("/start", status_code=status.HTTP_200_OK)
def start_simulation(
    payload: SimulationStartIn,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a synthetic simulation run and seed an initial event."""
    session = _get_owned_session(db, payload.session_id, current_user)
    _running[session.id] = payload.profile
    seeded = _persist(db, session.id, sim_service.generate_events(1, payload.profile))
    audit.record(
        db, user_id=current_user.id, action="simulation.start",
        detail=f"session_id={session.id} profile={payload.profile}",
    )
    return {
        "status": "RUNNING",
        "session_id": session.id,
        "profile": payload.profile,
        "seeded_event": SimulationEventOut.model_validate(seeded[0]),
    }


@router.post("/generate", response_model=list[SimulationEventOut])
def generate(
    payload: SimulationGenerateIn,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate one or more synthetic telemetry events for a session."""
    session = _get_owned_session(db, payload.session_id, current_user)
    rows = _persist(
        db, session.id, sim_service.generate_events(payload.count, payload.profile)
    )
    return rows


@router.post("/stop", status_code=status.HTTP_200_OK)
def stop_simulation(
    payload: SimulationStartIn,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop the synthetic simulation run for a session."""
    session = _get_owned_session(db, payload.session_id, current_user)
    _running.pop(session.id, None)
    audit.record(
        db, user_id=current_user.id, action="simulation.stop",
        detail=f"session_id={session.id}",
    )
    return {"status": "STOPPED", "session_id": session.id}


@router.get("/events", response_model=list[SimulationEventOut])
def list_events(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List synthetic telemetry events for a session."""
    session = _get_owned_session(db, session_id, current_user)
    rows = db.scalars(
        select(SimulationEvent)
        .where(SimulationEvent.session_id == session.id)
        .order_by(SimulationEvent.created_at.asc())
    ).all()
    return rows


@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_simulation(
    payload: SimulationStartIn,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all synthetic telemetry for a session and clear run state."""
    session = _get_owned_session(db, payload.session_id, current_user)
    db.execute(delete(SimulationEvent).where(SimulationEvent.session_id == session.id))
    db.commit()
    _running.pop(session.id, None)
    audit.record(
        db, user_id=current_user.id, action="simulation.reset",
        detail=f"session_id={session.id}",
    )
    return {"status": "RESET", "session_id": session.id}
