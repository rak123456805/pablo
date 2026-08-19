"""
CRUD and authorization integration tests.

These tests use the test HTTP client (which overrides the DB dependency).
They verify:
  - Role enforcement: editor can CRUD, cannot publish; unauthenticated is rejected
  - Business rules enforced in route handlers:
      * published show requires section
      * published episode requires duration
      * (content_group, language) uniqueness on create and update
  - Slug uniqueness on show create
  - Season uniqueness per show
  - Proper HTTP status codes
"""
from __future__ import annotations

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# Authentication / authorization
# ─────────────────────────────────────────────────────────────────────────────

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
    resp = await client.get("/api/v1/auth/me", headers=auth(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_cannot_list_shows(client):
    resp = await client.get("/api/v1/admin/shows")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_editor_can_list_shows(client, editor_token):
    resp = await client.get("/api/v1/admin/shows", headers=auth(editor_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_editor_cannot_publish(client, editor_token):
    """Publish endpoint requires admin role — editor must be rejected."""
    resp = await client.post(
        "/api/v1/admin/catalog/publish",
        headers=auth(editor_token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["db"] == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Show CRUD
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_show_draft_without_section(client, editor_token):
    """Draft shows can be created without a section."""
    resp = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={
            "slug": "test-show-draft",
            "title": "Test Show",
            "status": "draft",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["slug"] == "test-show-draft"
    assert data["section"] is None
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_create_show_published_requires_section(client, editor_token):
    """Published show must have a section — 422 if missing."""
    resp = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={
            "slug": "bad-published",
            "title": "Bad Published Show",
            "status": "published",
            # no section
        },
    )
    assert resp.status_code == 422
    assert "section" in resp.json()["detail"].lower() or "section" in resp.text.lower()


@pytest.mark.asyncio
async def test_create_show_published_with_section(client, editor_token):
    """Published show with valid section is accepted."""
    resp = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={
            "slug": "good-published",
            "title": "Good Published Show",
            "status": "published",
            "section": "series",
            "categories": ["adventure"],
        },
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_create_show_invalid_section_rejected(client, editor_token):
    """section must be one of the reference.json values."""
    resp = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={
            "slug": "bad-section",
            "title": "Bad Section",
            "section": "cartoons",  # not in reference.json
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_show_invalid_category_rejected(client, editor_token):
    """categories must all be from reference.json values."""
    resp = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={
            "slug": "bad-cat",
            "title": "Bad Category",
            "section": "series",
            "categories": ["adventure", "robots"],  # 'robots' not in reference.json
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_show_slug_uniqueness(client, editor_token):
    """Creating a show with a duplicate slug returns 409."""
    payload = {"slug": "unique-show", "title": "Unique Show"}
    resp1 = await client.post("/api/v1/admin/shows", headers=auth(editor_token), json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/admin/shows", headers=auth(editor_token), json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_update_show_to_published_without_section_rejected(client, editor_token):
    """Patching status to 'published' on a show without section is rejected."""
    create = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={"slug": "no-section-show", "title": "No Section"},
    )
    assert create.status_code == 201
    show_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/admin/shows/{show_id}",
        headers=auth(editor_token),
        json={"status": "published"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_show_set_section_then_publish(client, editor_token):
    """Adding section and then publishing in one PATCH should work."""
    create = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={"slug": "gradual-publish", "title": "Gradual Show"},
    )
    show_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/admin/shows/{show_id}",
        headers=auth(editor_token),
        json={"section": "series", "status": "published"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_delete_show(client, editor_token):
    create = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={"slug": "to-delete", "title": "To Delete"},
    )
    show_id = create.json()["id"]

    resp = await client.delete(f"/api/v1/admin/shows/{show_id}", headers=auth(editor_token))
    assert resp.status_code == 204

    get = await client.get(f"/api/v1/admin/shows/{show_id}", headers=auth(editor_token))
    assert get.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Season CRUD
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
async def show_id(client, editor_token):
    """Create and return the UUID of a test show."""
    resp = await client.post(
        "/api/v1/admin/shows",
        headers=auth(editor_token),
        json={"slug": "fixture-show", "title": "Fixture Show", "section": "series"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_season(client, editor_token, show_id):
    resp = await client.post(
        f"/api/v1/admin/shows/{show_id}/seasons",
        headers=auth(editor_token),
        json={"season_number": 1},
    )
    assert resp.status_code == 201
    assert resp.json()["season_number"] == 1


@pytest.mark.asyncio
async def test_create_season_zero(client, editor_token, show_id):
    """Season 0 (trailers) is allowed."""
    resp = await client.post(
        f"/api/v1/admin/shows/{show_id}/seasons",
        headers=auth(editor_token),
        json={"season_number": 0},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_season_uniqueness(client, editor_token, show_id):
    """Duplicate season_number for same show returns 409."""
    await client.post(
        f"/api/v1/admin/shows/{show_id}/seasons",
        headers=auth(editor_token),
        json={"season_number": 2},
    )
    resp2 = await client.post(
        f"/api/v1/admin/shows/{show_id}/seasons",
        headers=auth(editor_token),
        json={"season_number": 2},
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_list_seasons(client, editor_token, show_id):
    for n in [0, 1, 2]:
        await client.post(
            f"/api/v1/admin/shows/{show_id}/seasons",
            headers=auth(editor_token),
            json={"season_number": n},
        )
    resp = await client.get(
        f"/api/v1/admin/shows/{show_id}/seasons",
        headers=auth(editor_token),
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 3


# ─────────────────────────────────────────────────────────────────────────────
# Episode CRUD
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
async def season_id(client, editor_token, show_id):
    """Create season 1 for the test show, return its UUID."""
    resp = await client.post(
        f"/api/v1/admin/shows/{show_id}/seasons",
        headers=auth(editor_token),
        json={"season_number": 1},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_draft_episode_no_duration(client, editor_token, season_id):
    """Draft episodes can be created without duration_seconds."""
    resp = await client.post(
        "/api/v1/admin/episodes",
        headers=auth(editor_token),
        json={
            "season_id": season_id,
            "episode_number": 1,
            "title": "Draft Ep",
            "language": "en",
            "content_group": "test-cg-ep1",
            "status": "draft",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["duration_seconds"] is None


@pytest.mark.asyncio
async def test_create_published_episode_requires_duration(client, editor_token, season_id):
    """Published episode without duration_seconds must return 422."""
    resp = await client.post(
        "/api/v1/admin/episodes",
        headers=auth(editor_token),
        json={
            "season_id": season_id,
            "episode_number": 1,
            "title": "Bad Pub Ep",
            "language": "en",
            "content_group": "bad-pub-cg",
            "status": "published",
            # no duration_seconds
        },
    )
    assert resp.status_code == 422
    assert "duration" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_published_episode_with_duration(client, editor_token, season_id):
    """Published episode with duration is accepted."""
    resp = await client.post(
        "/api/v1/admin/episodes",
        headers=auth(editor_token),
        json={
            "season_id": season_id,
            "episode_number": 1,
            "title": "Good Pub Ep",
            "language": "en",
            "content_group": "good-pub-cg",
            "status": "published",
            "duration_seconds": 300,
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_episode_language_must_be_valid(client, editor_token, season_id):
    """Language must be one of the reference.json values."""
    resp = await client.post(
        "/api/v1/admin/episodes",
        headers=auth(editor_token),
        json={
            "season_id": season_id,
            "episode_number": 1,
            "title": "Bad Lang",
            "language": "fr",  # not in reference.json
            "content_group": "bad-lang-cg",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_content_group_language_uniqueness(client, editor_token, season_id):
    """Second episode with same (content_group, language) must return 409."""
    payload = {
        "season_id": season_id,
        "episode_number": 1,
        "title": "First",
        "language": "en",
        "content_group": "dup-test-cg",
    }
    r1 = await client.post("/api/v1/admin/episodes", headers=auth(editor_token), json=payload)
    assert r1.status_code == 201

    payload2 = {**payload, "episode_number": 2, "title": "Duplicate"}
    r2 = await client.post("/api/v1/admin/episodes", headers=auth(editor_token), json=payload2)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_update_episode_to_published_without_duration_rejected(client, editor_token, season_id):
    """Patching status to 'published' on a no-duration episode must fail."""
    create = await client.post(
        "/api/v1/admin/episodes",
        headers=auth(editor_token),
        json={
            "season_id": season_id,
            "episode_number": 1,
            "title": "Will Fail",
            "language": "en",
            "content_group": "fail-pub-cg",
            "status": "draft",
        },
    )
    ep_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/admin/episodes/{ep_id}",
        headers=auth(editor_token),
        json={"status": "published"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_episode_add_duration_then_publish(client, editor_token, season_id):
    """Patching duration and status together in one PATCH is allowed."""
    create = await client.post(
        "/api/v1/admin/episodes",
        headers=auth(editor_token),
        json={
            "season_id": season_id,
            "episode_number": 1,
            "title": "Will Publish",
            "language": "en",
            "content_group": "will-pub-cg",
            "status": "draft",
        },
    )
    ep_id = create.json()["id"]

    resp = await client.patch(
        f"/api/v1/admin/episodes/{ep_id}",
        headers=auth(editor_token),
        json={"duration_seconds": 240, "status": "published"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"


@pytest.mark.asyncio
async def test_update_episode_cg_lang_uniqueness(client, editor_token, season_id):
    """Patching (content_group, language) to match another episode returns 409."""
    # Create two episodes with different content_groups
    r1 = await client.post(
        "/api/v1/admin/episodes",
        headers=auth(editor_token),
        json={"season_id": season_id, "episode_number": 1, "title": "E1",
              "language": "en", "content_group": "cg-unique-a"},
    )
    r2 = await client.post(
        "/api/v1/admin/episodes",
        headers=auth(editor_token),
        json={"season_id": season_id, "episode_number": 2, "title": "E2",
              "language": "en", "content_group": "cg-unique-b"},
    )
    ep2_id = r2.json()["id"]

    # Try to update E2's content_group to match E1's
    resp = await client.patch(
        f"/api/v1/admin/episodes/{ep2_id}",
        headers=auth(editor_token),
        json={"content_group": "cg-unique-a"},  # would clash with E1
    )
    assert resp.status_code == 409
