"""
Auth endpoint tests — kept here as a focused auth-only suite.

The broader integration tests (CRUD business rules, role enforcement) live in
test_crud.py. This file covers the auth API surface specifically.
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email": admin_user.email, "password": "adminpass"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email": admin_user.email, "password": "wrongpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email": "nobody@peblo.tv", "password": "anything"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user(client, admin_token):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_editor_cannot_publish(client, editor_token):
    """Publish endpoint requires admin role."""
    resp = await client.post(
        "/api/v1/admin/catalog/publish",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_admin(client):
    resp = await client.get("/api/v1/admin/shows")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["db"] == "ok"
