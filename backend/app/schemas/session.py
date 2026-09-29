"""Session schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SessionStatus


class SessionCreate(BaseModel):
    label: str | None = Field(default=None, max_length=255)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    label: str | None
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None
    total_keystrokes: int
