"""SOC dashboard summary and live WebSocket routes."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.database import SessionLocal, get_db
from app.core.security import decode_access_token
from app.models.detection import DetectionResult
from app.models.enums import RiskLevel, SessionStatus
from app.models.keystroke import KeystrokeTestEvent
from app.models.session import Session
from app.models.simulation import SimulationEvent
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, TimelinePoint

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _build_summary(db: DBSession, user: User) -> DashboardSummary:
    session_ids = list(
        db.scalars(select(Session.id).where(Session.user_id == user.id)).all()
    )
    total_sessions = len(session_ids)

    # Latest detection result across the user's sessions.
    latest = None
    if session_ids:
        latest = db.scalars(
            select(DetectionResult)
            .where(DetectionResult.session_id.in_(session_ids))
            .order_by(DetectionResult.created_at.desc())
            .limit(1)
        ).first()

    risk_level = latest.risk_level if latest else RiskLevel.LOW
    risk_score = latest.risk_score if latest else 0
    rules_triggered = len(latest.triggered_rules) if latest else 0

    active_session = db.scalars(
        select(Session)
        .where(Session.user_id == user.id, Session.status == SessionStatus.ACTIVE)
        .order_by(Session.started_at.desc())
        .limit(1)
    ).first()

    total_keyboard = 0
    suspicious_processes = 0
    events_detected = 0
    if session_ids:
        total_keyboard = db.scalar(
            select(func.count(KeystrokeTestEvent.id)).where(
                KeystrokeTestEvent.session_id.in_(session_ids)
            )
        ) or 0
        events_detected = db.scalar(
            select(func.count(SimulationEvent.id)).where(
                SimulationEvent.session_id.in_(session_ids)
            )
        ) or 0
        suspicious_processes = db.scalar(
            select(func.count(func.distinct(SimulationEvent.process_name))).where(
                SimulationEvent.session_id.in_(session_ids),
                SimulationEvent.persistence_indicator.is_(True),
            )
        ) or 0

    # Recent timeline (last 15 mixed events).
    timeline: list[TimelinePoint] = []
    if session_ids:
        for s in db.scalars(
            select(SimulationEvent)
            .where(SimulationEvent.session_id.in_(session_ids))
            .order_by(SimulationEvent.created_at.desc())
            .limit(8)
        ).all():
            timeline.append(
                TimelinePoint(
                    timestamp=s.created_at,
                    label=f"Synthetic telemetry: {s.process_name}",
                    kind="simulation",
                )
            )
        for d in db.scalars(
            select(DetectionResult)
            .where(DetectionResult.session_id.in_(session_ids))
            .order_by(DetectionResult.created_at.desc())
            .limit(7)
        ).all():
            timeline.append(
                TimelinePoint(
                    timestamp=d.created_at,
                    label=f"Detection run — score {d.risk_score} ({d.risk_level.value})",
                    kind="detection",
                    severity=d.risk_level.value,
                )
            )
    timeline.sort(key=lambda p: p.timestamp, reverse=True)

    return DashboardSummary(
        current_risk_level=risk_level,
        current_risk_score=risk_score,
        events_detected=events_detected,
        active_test_session=active_session is not None,
        active_session_id=active_session.id if active_session else None,
        suspicious_processes=suspicious_processes,
        detection_rules_triggered=rules_triggered,
        total_keyboard_events=total_keyboard,
        simulation_status="RUNNING" if events_detected else "IDLE",
        total_sessions=total_sessions,
        timeline=timeline[:15],
    )


@router.get("/summary", response_model=DashboardSummary)
def summary(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated SOC dashboard summary for the current user."""
    return _build_summary(db, current_user)


@router.websocket("/ws")
async def dashboard_ws(websocket: WebSocket):
    """Live dashboard feed.

    The client connects with `?token=<JWT>`; the server pushes a fresh summary
    roughly every 5 seconds. This is a convenience channel for real-time UI
    updates — all authoritative data is also available via REST.
    """
    token = websocket.query_params.get("token")
    payload = decode_access_token(token) if token else None
    if not payload or payload.get("type") != "access":
        await websocket.close(code=1008)
        return
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                user = db.get(User, user_id)
                if user is None or not user.is_active:
                    await websocket.close(code=1008)
                    return
                summary_obj = _build_summary(db, user)
            finally:
                db.close()
            await websocket.send_text(summary_obj.model_dump_json())
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        return
