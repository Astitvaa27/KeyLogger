"""Detection engine & risk-scoring routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.detection import DetectionResult
from app.models.enums import RiskLevel
from app.models.session import Session
from app.models.simulation import SimulationEvent
from app.models.user import User
from app.schemas.detection import (
    DetectionAnalyzeIn,
    DetectionResultOut,
    DetectionRuleOut,
)
from app.services import audit
from app.services.detection import RULES, analyze

router = APIRouter(prefix="/detection", tags=["detection"])


def _get_owned_session(db: DBSession, session_id: int, user: User) -> Session:
    session = db.get(Session, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/rules", response_model=list[DetectionRuleOut])
def list_rules(current_user: User = Depends(get_current_user)):
    """Return the detection rule catalog (transparent scoring reference)."""
    return [
        DetectionRuleOut(
            rule_id=rid,
            name=r["name"],
            description=r["description"],
            severity=r["severity"],
            weight=r["weight"],
            recommendation=r["recommendation"],
        )
        for rid, r in RULES.items()
    ]


@router.post("/analyze", response_model=DetectionResultOut, status_code=status.HTTP_201_CREATED)
def analyze_session(
    payload: DetectionAnalyzeIn,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the detection engine over a session's synthetic telemetry."""
    session = _get_owned_session(db, payload.session_id, current_user)
    events = db.scalars(
        select(SimulationEvent).where(SimulationEvent.session_id == session.id)
    ).all()

    outcome = analyze(list(events))
    result = DetectionResult(
        session_id=session.id,
        risk_score=outcome["risk_score"],
        risk_level=RiskLevel(outcome["risk_level"]),
        triggered_rules=outcome["triggered_rules"],
        score_breakdown=outcome["score_breakdown"],
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    audit.record(
        db, user_id=current_user.id, action="detection.analyze",
        detail=f"session_id={session.id} score={result.risk_score}",
    )
    return result


@router.get("/results", response_model=list[DetectionResultOut])
def list_results(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List detection results for a session, newest first."""
    session = _get_owned_session(db, session_id, current_user)
    rows = db.scalars(
        select(DetectionResult)
        .where(DetectionResult.session_id == session.id)
        .order_by(DetectionResult.created_at.desc())
    ).all()
    return rows
