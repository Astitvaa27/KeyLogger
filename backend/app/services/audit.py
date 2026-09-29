"""Audit logging helper."""
from __future__ import annotations

from sqlalchemy.orm import Session as DBSession

from app.models.audit import AuditLog


def record(
    db: DBSession,
    *,
    user_id: int | None,
    action: str,
    detail: str | None = None,
    meta: dict | None = None,
    ip_address: str | None = None,
    commit: bool = True,
) -> AuditLog:
    """Persist an audit log entry for a security-relevant action."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        detail=detail,
        meta=meta,
        ip_address=ip_address,
    )
    db.add(entry)
    if commit:
        db.commit()
    return entry
