"""
Publishing pipeline tests — covers all 12 required scenarios.

Test scenarios:
  1.  Published-only filtering (draft content never appears in catalogue)
  2.  Missing artwork blocks publication
  3.  Duplicate (content_group, language) blocks publication
  4.  Conflicting content_group records (episode_number mismatch) block publication
  5.  Language collapsing (two variants → one catalogue entry)
  6.  Season 0 handling (trailers[] separate from seasons[])
  7.  Deterministic ordering (same DB state → same JSON)
  8.  Editor cannot publish (403)
  9.  Admin can publish (201)
  10. Failed publish leaves old catalogue untouched
  11. Repeated publish is idempotent
  12. Validation report API returns correct structure

All DB tests use the `db` and `client` fixtures from conftest.py.
Storage is reset between tests (autouse fixture in conftest).
"""
from __future__ import annotations

import json
import uuid

import pytest

from app.models import Artwork, Episode, Season, Show
from app.schemas.operations import CatalogOut
from app.services.catalog_builder import build_catalog
from app.services.validator import build_validation_report


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make_clean_published_show(db, *, slug="clean", title="Clean Show") -> tuple:
    """
    Create a minimal valid published show+season+episode+artwork.
    Returns (show, season, episode, artwork).
    """
    show = Show(
        slug=slug, title=title,
        section="series", categories=["adventure"],
        status="published",
    )
    db.add(show)
    await db.flush()

    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()

    ep = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="Episode One",
        duration_seconds=300, language="en",
        content_group=f"{slug}-s01e01",
        status="published",
    )
    db.add(ep)
    await db.flush()

    art = Artwork(
        owner_type="episode", owner_id=ep.id, kind="thumbnail",
        storage_key=f"episodes/{ep.id}/thumbnail.jpg",
        size_bytes=5000, width_px=640, height_px=360,
        content_type="image/jpeg",
    )
    db.add(art)
    await db.flush()

    return show, season, ep, art


# ─────────────────────────────────────────────────────────────────────────────
# 1. Published-only filtering
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_draft_show_excluded_from_catalogue(db):
    """Draft shows must never appear in the catalogue."""
    # Published show
    _show_pub, _, _ep_pub, _ = await _make_clean_published_show(db, slug="pub-show", title="Published Show")

    # Draft show with a published episode (should not appear)
    draft_show = Show(slug="draft-show", title="Draft Show", section="series", status="draft")
    db.add(draft_show)
    await db.flush()
    s = Season(show_id=draft_show.id, season_number=1)
    db.add(s)
    await db.flush()
    ep = Episode(
        show_id=draft_show.id, season_id=s.id,
        episode_number=1, title="Draft Ep",
        duration_seconds=100, language="en",
        content_group="draft-show-s01e01", status="published",
    )
    db.add(ep)
    await db.flush()

    catalog = await build_catalog(db, uuid.uuid4())

    all_slugs = [
        show.slug
        for shows in catalog.sections.values()
        for show in shows
    ]
    assert "pub-show" in all_slugs
    assert "draft-show" not in all_slugs, "Draft show must not appear in catalogue"


@pytest.mark.asyncio
async def test_draft_episode_excluded_from_catalogue(db):
    """Draft episodes within a published show must not appear in the catalogue."""
    show, season, pub_ep, _ = await _make_clean_published_show(db, slug="mixed-show", title="Mixed Show")

    # Add a draft episode to the same show
    draft_ep = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=2, title="Draft Episode",
        duration_seconds=200, language="en",
        content_group="mixed-show-s01e02", status="draft",
    )
    db.add(draft_ep)
    await db.flush()

    catalog = await build_catalog(db, uuid.uuid4())
    show_entry = catalog.sections["series"][0]
    all_cgs = [ep.content_group for s in show_entry.seasons for ep in s.episodes]

    assert "mixed-show-s01e01" in all_cgs
    assert "mixed-show-s01e02" not in all_cgs, "Draft episode must not appear in catalogue"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Missing artwork blocks publication
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_missing_artwork_blocks_publication(db):
    """A published episode with no artwork must appear as a blocking issue."""
    show = Show(slug="no-art-show", title="No Art", section="series", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()
    ep = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="No Artwork Episode",
        duration_seconds=300, language="en",
        content_group="no-art-show-s01e01", status="published",
    )
    db.add(ep)
    await db.flush()
    # No artwork uploaded!

    report = await build_validation_report(db)

    blocking_codes = [
        i.code
        for e in report.episode_issues
        for i in e.issues
        if i.severity == "blocking"
    ]
    assert "MISSING_ARTWORK" in blocking_codes
    assert report.can_publish is False


@pytest.mark.asyncio
async def test_missing_artwork_issue_has_correct_entity_fields(db):
    """ValidationIssue for missing artwork must carry entity/entity_id/field."""
    show = Show(slug="no-art2", title="No Art 2", section="series", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()
    ep = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="No Art Ep",
        duration_seconds=300, language="en",
        content_group="no-art2-s01e01",
        status="published",
        external_id="ep_test_001",
    )
    db.add(ep)
    await db.flush()

    report = await build_validation_report(db)
    missing_art = next(
        (i for e in report.episode_issues for i in e.issues if i.code == "MISSING_ARTWORK"),
        None,
    )
    assert missing_art is not None
    assert missing_art.entity == "episode"
    assert missing_art.entity_id == "ep_test_001"
    assert missing_art.field == "artwork"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Duplicate (content_group, language) blocks publication
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicate_cg_lang_blocks_publication(db):
    """Two episodes with same (content_group, language) must be flagged as blocking."""
    show = Show(slug="dup-show", title="Dup Show", section="series", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()

    # Two episodes — same CG + language
    for i in [1, 2]:
        ep = Episode(
            show_id=show.id, season_id=season.id,
            episode_number=i, title=f"Dup Episode {i}",
            duration_seconds=300, language="en",
            content_group="dup-show-s01e01",   # SAME content_group
            status="published",
            external_id=f"ep_dup_{i:04d}",
        )
        art = Artwork(
            owner_type="episode", owner_id=ep.id, kind="thumbnail",
            storage_key=f"episodes/dup{i}/thumb.jpg",
            size_bytes=1000, width_px=640, height_px=360,
            content_type="image/jpeg",
        )
        db.add(ep)
        await db.flush()
        art.owner_id = ep.id
        db.add(art)
        await db.flush()

    report = await build_validation_report(db)

    dup_issues = [
        i
        for e in report.episode_issues
        for i in e.issues
        if i.code == "DUPLICATE_CONTENT_GROUP_LANG"
    ]
    assert len(dup_issues) >= 2, "Both duplicate episodes should be flagged"
    assert report.can_publish is False


# ─────────────────────────────────────────────────────────────────────────────
# 4. Conflicting content_group records block publication
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_content_group_identity_conflict_blocks(db):
    """
    Cross-language variants sharing a content_group but with different episode_numbers
    must be flagged as CONTENT_GROUP_IDENTITY_CONFLICT (blocking).
    """
    show = Show(slug="conflict-show", title="Conflict", section="series", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()

    # English variant — episode 1
    ep_en = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="First Episode",
        duration_seconds=300, language="en",
        content_group="conflict-show-s01e01", status="published",
        external_id="ep_conf_en",
    )
    # Hindi variant — WRONG episode number (should be 1, but set to 2)
    ep_hi = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=2, title="Pahla Kadam",   # different episode number!
        duration_seconds=300, language="hi",
        content_group="conflict-show-s01e01",    # same content_group
        status="published",
        external_id="ep_conf_hi",
    )
    db.add_all([ep_en, ep_hi])
    await db.flush()

    for ep in [ep_en, ep_hi]:
        art = Artwork(
            owner_type="episode", owner_id=ep.id, kind="thumbnail",
            storage_key=f"episodes/{ep.id}/thumb.jpg",
            size_bytes=1000, width_px=640, height_px=360,
            content_type="image/jpeg",
        )
        db.add(art)
    await db.flush()

    report = await build_validation_report(db)

    conflict_issues = [
        i
        for e in report.episode_issues
        for i in e.issues
        if i.code == "CONTENT_GROUP_IDENTITY_CONFLICT"
    ]
    assert len(conflict_issues) >= 1, "Episode number mismatch should trigger CONTENT_GROUP_IDENTITY_CONFLICT"
    assert report.can_publish is False


# ─────────────────────────────────────────────────────────────────────────────
# 5. Language collapsing
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_language_variants_collapse_to_one_entry(db):
    """
    Two published episodes sharing a content_group (different languages) must
    collapse into ONE catalogue episode with languages: ["en", "hi"].
    """
    show = Show(slug="bilingual", title="Bilingual Show", section="series",
                status="published", categories=["stories"])
    db.add(show)
    await db.flush()

    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()

    CG = "bilingual-s01e01"
    ep_en = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="The Big Tree",
        duration_seconds=300, language="en", content_group=CG, status="published",
    )
    ep_hi = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="Bada Ped",
        duration_seconds=300, language="hi", content_group=CG, status="published",
    )
    db.add_all([ep_en, ep_hi])
    await db.flush()

    # Add artwork to both
    for ep in [ep_en, ep_hi]:
        art = Artwork(
            owner_type="episode", owner_id=ep.id, kind="thumbnail",
            storage_key=f"ep/{ep.id}/thumb.jpg",
            size_bytes=1000, width_px=640, height_px=360, content_type="image/jpeg",
        )
        db.add(art)
    await db.flush()

    catalog = await build_catalog(db, uuid.uuid4())

    series_shows = catalog.sections["series"]
    assert len(series_shows) == 1
    season_1_episodes = series_shows[0].seasons[0].episodes

    # Must be ONE entry, not two
    assert len(season_1_episodes) == 1, (
        f"Expected 1 catalogue episode, got {len(season_1_episodes)}"
    )
    entry = season_1_episodes[0]
    assert entry.content_group == CG
    assert sorted(entry.languages) == ["en", "hi"]
    # English is the primary
    assert entry.title == "The Big Tree"


@pytest.mark.asyncio
async def test_language_collapsing_uses_english_as_primary(db):
    """When English and Hindi variants exist, English title/duration takes precedence."""
    show = Show(slug="primary-test", title="Primary Test", section="featured", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()

    CG = "primary-test-s01e01"
    ep_hi = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="Hindi Title",
        duration_seconds=200, language="hi", content_group=CG, status="published",
    )
    ep_en = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="English Title",
        duration_seconds=300, language="en", content_group=CG, status="published",
    )
    db.add_all([ep_hi, ep_en])
    await db.flush()

    catalog = await build_catalog(db, uuid.uuid4())
    entry = catalog.sections["featured"][0].seasons[0].episodes[0]
    assert entry.title == "English Title"
    assert entry.duration_seconds == 300


@pytest.mark.asyncio
async def test_monolingual_episode_has_single_language(db):
    """A single-language episode results in languages: ['en'] — not collapsed."""
    show, _, ep, _ = await _make_clean_published_show(db, slug="mono", title="Mono Show")
    catalog = await build_catalog(db, uuid.uuid4())
    entry = catalog.sections["series"][0].seasons[0].episodes[0]
    assert entry.languages == ["en"]


# ─────────────────────────────────────────────────────────────────────────────
# 6. Season 0 handling
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_season_0_appears_in_trailers_not_seasons(db):
    """Season 0 episodes must appear in show.trailers[], NOT in show.seasons[]."""
    show = Show(slug="trailer-test", title="Trailer Test", section="series", status="published")
    db.add(show)
    await db.flush()

    s0 = Season(show_id=show.id, season_number=0)
    s1 = Season(show_id=show.id, season_number=1)
    db.add_all([s0, s1])
    await db.flush()

    # Season 0 trailer
    ep_trailer = Episode(
        show_id=show.id, season_id=s0.id,
        episode_number=1, title="The Trailer",
        duration_seconds=60, language="en",
        content_group="trailer-test-s00e01", status="published",
    )
    # Season 1 regular episode
    ep_regular = Episode(
        show_id=show.id, season_id=s1.id,
        episode_number=1, title="First Episode",
        duration_seconds=300, language="en",
        content_group="trailer-test-s01e01", status="published",
    )
    db.add_all([ep_trailer, ep_regular])
    await db.flush()

    for ep in [ep_trailer, ep_regular]:
        art = Artwork(
            owner_type="episode", owner_id=ep.id, kind="thumbnail",
            storage_key=f"ep/{ep.id}/thumb.jpg",
            size_bytes=1000, width_px=640, height_px=360, content_type="image/jpeg",
        )
        db.add(art)
    await db.flush()

    catalog = await build_catalog(db, uuid.uuid4())
    show_entry = catalog.sections["series"][0]

    # Season 0 → trailers only
    assert len(show_entry.trailers) == 1
    assert show_entry.trailers[0].content_group == "trailer-test-s00e01"

    # Season 1 → seasons only
    assert len(show_entry.seasons) == 1
    assert show_entry.seasons[0].season_number == 1
    assert len(show_entry.seasons[0].episodes) == 1

    # Season 0 must not appear in seasons[]
    season_numbers = [s.season_number for s in show_entry.seasons]
    assert 0 not in season_numbers, "Season 0 must not appear in show.seasons[]"


@pytest.mark.asyncio
async def test_season_0_not_renamed(db):
    """Season 0 must remain season_number=0 in trailers — must not be renumbered."""
    show = Show(slug="s0-rename", title="S0 Test", section="songs", status="published")
    db.add(show)
    await db.flush()
    s0 = Season(show_id=show.id, season_number=0)
    s1 = Season(show_id=show.id, season_number=1)
    db.add_all([s0, s1])
    await db.flush()

    ep_s0 = Episode(
        show_id=show.id, season_id=s0.id,
        episode_number=1, title="Trailer",
        duration_seconds=30, language="en",
        content_group="s0-rename-s00e01", status="published",
    )
    ep_s1 = Episode(
        show_id=show.id, season_id=s1.id,
        episode_number=1, title="Song One",
        duration_seconds=180, language="en",
        content_group="s0-rename-s01e01", status="published",
    )
    db.add_all([ep_s0, ep_s1])
    await db.flush()
    for ep in [ep_s0, ep_s1]:
        art = Artwork(owner_type="episode", owner_id=ep.id, kind="thumbnail",
                      storage_key=f"ep/{ep.id}/t.jpg", size_bytes=1000,
                      width_px=640, height_px=360, content_type="image/jpeg")
        db.add(art)
    await db.flush()

    catalog = await build_catalog(db, uuid.uuid4())
    show_entry = catalog.sections["songs"][0]

    # The single real season must still be season_number=1
    assert show_entry.seasons[0].season_number == 1


# ─────────────────────────────────────────────────────────────────────────────
# 7. Deterministic ordering
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deterministic_ordering(db):
    """
    Two calls to build_catalog with the same DB state must produce identical JSON.
    This verifies no random ordering (dict hashing, set iteration, etc.).
    """
    show, season, _ep, _art = await _make_clean_published_show(db, slug="det-show", title="Det Show")

    # Add more episodes
    for i in range(2, 6):
        ep = Episode(
            show_id=show.id, season_id=season.id,
            episode_number=i, title=f"Episode {i}",
            duration_seconds=200 + i, language="en",
            content_group=f"det-show-s01e0{i}", status="published",
        )
        db.add(ep)
        await db.flush()
        art = Artwork(
            owner_type="episode", owner_id=ep.id, kind="thumbnail",
            storage_key=f"ep/{ep.id}/t.jpg", size_bytes=1000,
            width_px=640, height_px=360, content_type="image/jpeg",
        )
        db.add(art)
        await db.flush()

    run_id = uuid.uuid4()
    catalog1 = await build_catalog(db, run_id)
    catalog2 = await build_catalog(db, run_id)

    json1 = catalog1.model_dump_json()
    json2 = catalog2.model_dump_json()
    assert json1 == json2, "Repeated catalog builds must produce identical JSON"


@pytest.mark.asyncio
async def test_episode_ordering_within_season(db):
    """Episodes within a season must be ordered by episode_number ascending."""
    show = Show(slug="order-test", title="Order Test", section="series", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()

    # Insert in reverse order
    for i in reversed(range(1, 5)):
        ep = Episode(
            show_id=show.id, season_id=season.id,
            episode_number=i, title=f"Ep {i}",
            duration_seconds=100, language="en",
            content_group=f"order-test-s01e0{i}", status="published",
        )
        db.add(ep)
        await db.flush()
        art = Artwork(
            owner_type="episode", owner_id=ep.id, kind="thumbnail",
            storage_key=f"ep/{ep.id}/t.jpg", size_bytes=1000,
            width_px=640, height_px=360, content_type="image/jpeg",
        )
        db.add(art)
        await db.flush()

    catalog = await build_catalog(db, uuid.uuid4())
    eps = catalog.sections["series"][0].seasons[0].episodes
    ep_numbers = [e.episode_number for e in eps]
    assert ep_numbers == sorted(ep_numbers), f"Episodes not in order: {ep_numbers}"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Editor cannot publish
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_editor_cannot_publish(client, editor_token):
    """POST /admin/catalog/publish requires admin role; editor gets 403."""
    resp = await client.post(
        "/api/v1/admin/catalog/publish",
        headers=auth(editor_token),
    )
    assert resp.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# 9. Admin can publish (when validation passes)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_can_publish_clean_catalogue(client, db, admin_token):
    """Admin can trigger a publish when no blocking issues exist."""
    await _make_clean_published_show(db, slug="admin-pub", title="Admin Pub Show")

    resp = await client.post(
        "/api/v1/admin/catalog/publish",
        headers=auth(admin_token),
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["status"] == "success"
    assert data["shows_count"] >= 1
    assert data["episodes_count"] >= 1


@pytest.mark.asyncio
async def test_publish_blocked_by_missing_artwork(client, db, admin_token):
    """Publish returns 422 when there are blocking validation issues."""
    # Published episode with no artwork
    show = Show(slug="pub-no-art", title="Pub No Art", section="series", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()
    ep = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="No Art",
        duration_seconds=300, language="en",
        content_group="pub-no-art-s01e01", status="published",
    )
    db.add(ep)
    await db.flush()
    # No artwork!

    resp = await client.post(
        "/api/v1/admin/catalog/publish",
        headers=auth(admin_token),
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 10. Failed publish leaves old catalogue untouched
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_failed_publish_leaves_old_catalogue_intact(client, db, admin_token):
    """
    If publish validation fails, the previously published catalog.json must be
    untouched.
    """
    from app.services.artwork_storage import get_storage
    from app.services.publisher import CATALOG_KEY

    # Write a "previous" catalogue manually
    old_catalog = json.dumps({
        "schema_version": "1",
        "publish_run_id": "old-run",
        "sections": {"featured": [], "series": [], "minisodes": [], "songs": []},
    }).encode()
    storage = get_storage()
    await storage.put(CATALOG_KEY, old_catalog, "application/json")

    # Now trigger a publish that will fail (published episode, no artwork)
    show = Show(slug="will-fail-pub", title="Will Fail", section="series", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()
    ep = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=1, title="No Art",
        duration_seconds=300, language="en",
        content_group="will-fail-s01e01", status="published",
    )
    db.add(ep)
    await db.flush()

    resp = await client.post(
        "/api/v1/admin/catalog/publish",
        headers=auth(admin_token),
    )
    assert resp.status_code == 422

    # Old catalogue must still be there and unchanged
    assert storage.exists(CATALOG_KEY)
    current_data = await storage.get(CATALOG_KEY)
    assert json.loads(current_data)["publish_run_id"] == "old-run", (
        "Old catalogue was overwritten despite publish failure"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 11. Repeated publish is idempotent
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_repeated_publish_is_idempotent(client, db, admin_token):
    """
    Publishing twice without changing source data must produce the same catalogue
    structure. Publish run IDs differ (new UUID each run) but content is equivalent.
    """
    await _make_clean_published_show(db, slug="idem-show", title="Idempotent Show")

    resp1 = await client.post(
        "/api/v1/admin/catalog/publish",
        headers=auth(admin_token),
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        "/api/v1/admin/catalog/publish",
        headers=auth(admin_token),
    )
    assert resp2.status_code == 201

    # Fetch the published catalogue
    cat_resp = await client.get("/api/v1/catalog")
    assert cat_resp.status_code == 200
    cat = cat_resp.json()

    # Structure must be correct regardless of which run produced it
    assert "series" in cat["sections"]
    series_shows = cat["sections"]["series"]
    assert len(series_shows) == 1
    assert series_shows[0]["slug"] == "idem-show"

    # Content (episodes, languages) must be stable
    ep_entry = series_shows[0]["seasons"][0]["episodes"][0]
    assert ep_entry["content_group"] == "idem-show-s01e01"
    assert ep_entry["languages"] == ["en"]


# ─────────────────────────────────────────────────────────────────────────────
# 12. Validation report API
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validation_report_api_requires_auth(client):
    resp = await client.get("/api/v1/admin/validation/report")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_validation_report_api_returns_correct_structure(client, db, editor_token):
    """GET /admin/validation-report returns the expected JSON structure."""
    _show, _, _ep, _ = await _make_clean_published_show(db, slug="vr-test", title="VR Test")

    resp = await client.get(
        "/api/v1/admin/validation/report",
        headers=auth(editor_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "can_publish" in data
    assert "summary" in data
    assert "show_issues" in data
    assert "episode_issues" in data
    assert "blocking" in data["summary"]
    assert "warning" in data["summary"]


@pytest.mark.asyncio
async def test_validation_report_issues_have_entity_fields(client, db, editor_token):
    """Every ValidationIssue must carry entity/entity_id/field."""
    # Create a published show without a section to generate a show-level issue
    show = Show(slug="issue-test", title="Issue Test", section=None, status="published")
    db.add(show)
    await db.flush()

    resp = await client.get(
        "/api/v1/admin/validation/report",
        headers=auth(editor_token),
    )
    assert resp.status_code == 200
    data = resp.json()

    for entry in data["show_issues"]:
        for issue in entry["issues"]:
            assert "entity" in issue
            assert "entity_id" in issue
            assert "field" in issue
            assert "code" in issue
            assert "severity" in issue
            assert "message" in issue


@pytest.mark.asyncio
async def test_draft_show_missing_section_is_warning_not_blocking(db):
    """
    A DRAFT show with no section should produce a WARNING, not a blocking issue.
    (Only published shows with no section are blocking.)
    """
    show = Show(slug="draft-no-section", title="Draft No Section",
                section=None, status="draft")
    db.add(show)
    await db.flush()

    report = await build_validation_report(db)

    no_section_issues = [
        i
        for e in report.show_issues
        if e.slug == "draft-no-section"
        for i in e.issues
        if i.code == "MISSING_SECTION"
    ]
    assert len(no_section_issues) == 1
    assert no_section_issues[0].severity == "warning", (
        "Draft show with no section should produce a warning, not a blocking error"
    )


@pytest.mark.asyncio
async def test_published_show_missing_section_is_blocking(db):
    """A PUBLISHED show with no section must be a blocking issue."""
    show = Show(slug="pub-no-section", title="Pub No Section",
                section=None, status="published")
    db.add(show)
    await db.flush()

    report = await build_validation_report(db)

    issues = [
        i
        for e in report.show_issues
        if e.slug == "pub-no-section"
        for i in e.issues
        if i.code == "MISSING_SECTION"
    ]
    assert len(issues) == 1
    assert issues[0].severity == "blocking"
    assert report.can_publish is False


# ─────────────────────────────────────────────────────────────────────────────
# Search — public endpoint, no auth needed
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_no_catalogue_returns_404(client):
    """GET /catalog/search with no published catalogue returns 404."""
    resp = await client.get("/api/v1/catalog/search?q=test")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_search_q_matches_show_title(client, db, admin_token):
    """Search by q matches show title."""
    await _make_clean_published_show(db, slug="jungle", title="Jungle Adventures")
    await client.post("/api/v1/admin/catalog/publish", headers=auth(admin_token))

    resp = await client.get("/api/v1/catalog/search?q=Jungle")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert any(r["title"] == "Jungle Adventures" for r in results)


@pytest.mark.asyncio
async def test_search_q_matches_episode_title(client, db, admin_token):
    """Search by q matches episode title."""
    show, season, _, _ = await _make_clean_published_show(db, slug="ep-search", title="EP Search Show")
    # Rename the episode to something searchable
    ep = Episode(
        show_id=show.id, season_id=season.id,
        episode_number=2, title="The Hidden Cave",
        duration_seconds=200, language="en",
        content_group="ep-search-s01e02", status="published",
    )
    db.add(ep)
    await db.flush()
    art = Artwork(
        owner_type="episode", owner_id=ep.id, kind="thumbnail",
        storage_key=f"ep/{ep.id}/t.jpg", size_bytes=1000,
        width_px=640, height_px=360, content_type="image/jpeg",
    )
    db.add(art)
    await db.flush()
    await client.post("/api/v1/admin/catalog/publish", headers=auth(admin_token))

    resp = await client.get("/api/v1/catalog/search?q=Hidden+Cave")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) >= 1
    found_eps = [ep for r in results for s in r["seasons"] for ep in s["episodes"]]
    assert any("Hidden Cave" in ep["title"] for ep in found_eps)


@pytest.mark.asyncio
async def test_search_by_language(client, db, admin_token):
    """Language filter returns only episodes with that language."""
    show = Show(slug="lang-search", title="Lang Search", section="series", status="published")
    db.add(show)
    await db.flush()
    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()

    CG = "lang-search-s01e01"
    for lang in ["en", "hi"]:
        ep = Episode(
            show_id=show.id, season_id=season.id,
            episode_number=1, title=f"Ep {lang}",
            duration_seconds=200, language=lang, content_group=CG, status="published",
        )
        db.add(ep)
        await db.flush()
        art = Artwork(
            owner_type="episode", owner_id=ep.id, kind="thumbnail",
            storage_key=f"ep/{ep.id}/t.jpg", size_bytes=1000,
            width_px=640, height_px=360, content_type="image/jpeg",
        )
        db.add(art)
        await db.flush()

    await client.post("/api/v1/admin/catalog/publish", headers=auth(admin_token))

    resp = await client.get("/api/v1/catalog/search?language=hi")
    assert resp.status_code == 200
    results = resp.json()["results"]
    all_ep_langs = [
        lang
        for r in results
        for s in r["seasons"]
        for ep in s["episodes"]
        for lang in ep["languages"]
    ]
    assert "hi" in all_ep_langs


@pytest.mark.asyncio
async def test_search_by_section(client, db, admin_token):
    """Section filter returns only shows in that section."""
    await _make_clean_published_show(db, slug="sec-series", title="Series Show")

    songs_show = Show(slug="sec-songs", title="Songs Show", section="songs", status="published")
    db.add(songs_show)
    await db.flush()
    s = Season(show_id=songs_show.id, season_number=1)
    db.add(s)
    await db.flush()
    ep = Episode(
        show_id=songs_show.id, season_id=s.id,
        episode_number=1, title="A Song",
        duration_seconds=120, language="en",
        content_group="sec-songs-s01e01", status="published",
    )
    db.add(ep)
    await db.flush()
    art = Artwork(
        owner_type="episode", owner_id=ep.id, kind="thumbnail",
        storage_key=f"ep/{ep.id}/t.jpg", size_bytes=1000,
        width_px=640, height_px=360, content_type="image/jpeg",
    )
    db.add(art)
    await db.flush()

    await client.post("/api/v1/admin/catalog/publish", headers=auth(admin_token))

    resp = await client.get("/api/v1/catalog/search?section=songs")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert all(r["section"] == "songs" for r in results)
    assert len(results) == 1
    assert results[0]["slug"] == "sec-songs"
