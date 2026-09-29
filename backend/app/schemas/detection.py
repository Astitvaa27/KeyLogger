"""Detection & risk-scoring schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import RiskLevel, Severity


class DetectionRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    name: str
    description: str
    severity: Severity
    weight: int
    recommendation: str


class TriggeredRule(BaseModel):
    rule_id: str
    name: str
    description: str
    severity: Severity
    evidence: str
    recommendation: str
    contribution: int
    timestamp: datetime


class DetectionAnalyzeIn(BaseModel):
    session_id: int


class DetectionResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    risk_score: int
    risk_level: RiskLevel
    triggered_rules: list[dict]
    score_breakdown: dict
    created_at: datetime
