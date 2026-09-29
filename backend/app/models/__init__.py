"""ORM models package.

Importing everything here ensures all models are registered on the shared
`Base.metadata` (needed by Alembic autogenerate and by create_all in tests).
"""
from app.models.audit import AuditLog
from app.models.detection import DetectionResult, DetectionRule
from app.models.enums import (
    KeyCategory,
    RiskLevel,
    Severity,
    SessionStatus,
    SimulationStatus,
)
from app.models.keystroke import KeystrokeTestEvent
from app.models.session import Session
from app.models.simulation import SimulationEvent
from app.models.user import User

__all__ = [
    "AuditLog",
    "DetectionResult",
    "DetectionRule",
    "KeystrokeTestEvent",
    "Session",
    "SimulationEvent",
    "User",
    "KeyCategory",
    "RiskLevel",
    "Severity",
    "SessionStatus",
    "SimulationStatus",
]
