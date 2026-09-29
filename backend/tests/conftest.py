"""Shared pytest fixtures.

Tests run against an isolated in-memory SQLite database so they need no live
PostgreSQL server and never touch development data. The FastAPI `get_db`
dependency is overridden to use the test session.
"""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register all tables on Base.metadata)
from app.core.database import Base, get_db
from app.main import app as fastapi_app


@pytest.fixture()
def db_engine():
    # StaticPool + shared in-memory connection so all sessions see one schema.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_engine):
    TestingSession = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Register a user and return Authorization headers for it."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "tester@example.com",
            "username": "tester",
            "password": "TestPass123!",
            "full_name": "Test User",
        },
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def active_session(client, auth_headers):
    """Create and return an active session id."""
    resp = client.post("/api/sessions/start", json={"label": "test"}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
