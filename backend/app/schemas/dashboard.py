"""SOC dashboard summary schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import RiskLevel


class TimelinePoint(BaseModel):
    timestamp: datetime
    label: str
    kind: str  # "keystroke" | "simulation" | "detection"
    severity: str | None = None


class DashboardSummary(BaseModel):
    current_risk_level: RiskLevel
    current_risk_score: int
    events_detected: int
    active_test_session: bool
    active_session_id: int | None
    suspicious_processes: int
    detection_rules_triggered: int
    total_keyboard_events: int
    simulation_status: str
    total_sessions: int
    timeline: list[TimelinePoint]
