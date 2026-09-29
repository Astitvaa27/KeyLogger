"""Health check route."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Liveness + database connectivity check."""
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - depends on live DB
        db_ok = False
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "ok" if db_ok else "unavailable",
    }
