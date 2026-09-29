"""FastAPI application entrypoint for the KeyLogger platform.

Assembles middleware (CORS), mounts the API router, seeds reference data, and
exposes a friendly root endpoint. Keystroke handling here concerns only
in-app test metadata — see the project README for the safety scope.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.utils.seed import seed_detection_rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed the detection-rule catalog on startup (idempotent). Failures here are
    # non-fatal so the app can still boot before migrations have been applied.
    try:
        db = SessionLocal()
        try:
            seed_detection_rules(db)
        finally:
            db.close()
    except Exception:  # pragma: no cover - depends on live DB
        pass
    yield


app = FastAPI(
    title="KeyLogger — Keylogging Detection & Behavioral Analysis Platform",
    description=(
        "Defensive, educational platform: virtual keystroke lab, synthetic "
        "threat simulation, rule-based detection, transparent risk scoring, "
        "and a SOC-style dashboard. Contains no real keylogging capability."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["root"])
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "notice": "Educational defensive platform — no real keylogging.",
    }
