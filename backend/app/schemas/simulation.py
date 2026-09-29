"""Synthetic threat simulation schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SimulationStartIn(BaseModel):
    session_id: int
    # Optional preset controlling how "aggressive" the synthetic telemetry is.
    profile: str = Field(default="balanced", pattern="^(benign|balanced|aggressive)$")


class SimulationGenerateIn(BaseModel):
    session_id: int
    count: int = Field(default=1, ge=1, le=100)
    profile: str = Field(default="balanced", pattern="^(benign|balanced|aggressive)$")


class SimulationEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    process_name: str
    keyboard_events: int
    persistence_indicator: bool
    network_activity: bool
    event_rate_per_min: int
    risk_indicators: list[str]
    created_at: datetime
