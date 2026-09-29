"""Aggregate API router mounting all route modules under /api."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    auth,
    dashboard,
    detection,
    health,
    keystrokes,
    sessions,
    simulation,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(sessions.router)
api_router.include_router(keystrokes.router)
api_router.include_router(simulation.router)
api_router.include_router(detection.router)
api_router.include_router(dashboard.router)
