"""Integration tests for authentication endpoints."""
from __future__ import annotations


def test_register_and_me(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "a@example.com",
            "username": "alice",
            "password": "AlicePass1!",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "alice"

    token = body["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "a@example.com"


def test_duplicate_registration_conflicts(client):
    payload = {"email": "dup@example.com", "username": "dup", "password": "DupPass12!"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_login_with_username_and_email(client):
    client.post(
        "/api/auth/register",
        json={"email": "b@example.com", "username": "bob", "password": "BobPass123!"},
    )
    for identifier in ("bob", "b@example.com"):
        resp = client.post(
            "/api/auth/login",
            json={"username_or_email": identifier, "password": "BobPass123!"},
        )
        assert resp.status_code == 200, identifier
        assert resp.json()["access_token"]


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "c@example.com", "username": "carol", "password": "CarolPass1!"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username_or_email": "carol", "password": "nope"},
    )
    assert resp.status_code == 401


def test_short_password_rejected(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "d@example.com", "username": "dave", "password": "short"},
    )
    assert resp.status_code == 422  # Pydantic validation


def test_protected_route_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/dashboard/summary").status_code == 401


def test_invalid_token_rejected(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401
