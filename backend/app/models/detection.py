"""Detection rule catalog and detection result models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RiskLevel, Severity

if TYPE_CHECKING:
    from app.models.session import Session


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DetectionRule(Base):
    """Catalog of rule-based detection rules (seeded, reference data)."""

    __tablename__ = "detection_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(SAEnum(Severity), nullable=False)
    # Points this rule contributes to the risk score when it fires.
    weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DetectionRule {self.rule_id} sev={self.severity}>"


class DetectionResult(Base):
    """Outcome of running the detection engine over a session's telemetry."""

    __tablename__ = "detection_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(SAEnum(RiskLevel), nullable=False)
    # Full triggered-rule breakdown: list of dicts with rule_id, severity,
    # evidence, recommendation, contribution.
    triggered_rules: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # Transparent per-rule score contributions: {rule_id: points}.
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    session: Mapped["Session"] = relationship(back_populates="detection_results")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DetectionResult score={self.risk_score} level={self.risk_level}>"
