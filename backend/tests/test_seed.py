"""
Seed importer tests — verifies all 95 rows are accounted for,
anomalies are detected, and bad data is preserved (not silently fixed).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.models import Episode, Season, Show
from app.services.seed_importer import import_seed_file

SEED_PATH = Path(__file__).parent.parent.parent / "seed_shows.json"


@pytest.mark.asyncio
async def test_seed_imports_all_rows(db):
    """All 95 seed rows are accounted for (95 episodes created or in anomaly log)."""
    result = await import_seed_file(db, SEED_PATH)
    total_accounted = result.episodes_created + result.episodes_skipped
    assert result.rows_total == 95
    assert total_accounted == 95, (
        f"Expected 95 rows accounted for, got {total_accounted} "
        f"(created={result.episodes_created}, skipped={result.episodes_skipped})"
    )


@pytest.mark.asyncio
async def test_seed_creates_8_shows(db):
    """Seed data has 8 unique shows — deduplicated by slug."""
    await import_seed_file(db, SEED_PATH)
    count = await db.execute(select(func.count(Show.id)))
    assert count.scalar_one() == 8


@pytest.mark.asyncio
async def test_seed_creates_correct_season_counts(db):
    """Check season counts per show match expected structure."""
    await import_seed_file(db, SEED_PATH)

    # Shows with season 0 trailers
    shows_with_s0 = await db.execute(
        select(Season).where(Season.season_number == 0)
    )
    s0_seasons = list(shows_with_s0.scalars().all())
    # ep_0093 (Moti's Many Lives S0) and ep_0094 (Tiny Tales S0)
    assert len(s0_seasons) == 2, f"Expected 2 Season-0 seasons, got {len(s0_seasons)}"


@pytest.mark.asyncio
async def test_seed_detects_rhyme_rangers_null_section(db):
    """Rhyme Rangers has null section — anomaly is detected and show is preserved."""
    result = await import_seed_file(db, SEED_PATH)

    # Check the show exists with null section
    show_result = await db.execute(select(Show).where(Show.slug == "rhyme-rangers"))
    show = show_result.scalar_one_or_none()
    assert show is not None, "Rhyme Rangers show should be imported"
    assert show.section is None, "Rhyme Rangers section should remain null"

    # Check anomaly was detected
    null_section_anomalies = [
        a for a in result.anomalies if a.anomaly_type == "MISSING_SECTION"
    ]
    assert len(null_section_anomalies) > 0, "MISSING_SECTION anomaly should be detected"


@pytest.mark.asyncio
async def test_seed_detects_duplicate_content_group_lang(db):
    """ep_9001 duplicates ep_0004 on (content_group, language) — anomaly detected."""
    result = await import_seed_file(db, SEED_PATH)

    dupe_anomalies = [
        a for a in result.anomalies if a.anomaly_type == "DUPLICATE_CONTENT_GROUP_LANG"
    ]
    assert len(dupe_anomalies) >= 1, "Duplicate (content_group, language) anomaly should be detected"
    # ep_9001 should be involved
    ep9001_anomaly = next(
        (a for a in dupe_anomalies if a.episode_id == "ep_9001"), None
    )
    assert ep9001_anomaly is not None, "ep_9001 should be flagged as duplicate"


@pytest.mark.asyncio
async def test_seed_detects_published_no_artwork(db):
    """ep_0036 is published with empty artwork_available — anomaly detected."""
    result = await import_seed_file(db, SEED_PATH)

    no_art_anomalies = [
        a for a in result.anomalies if a.anomaly_type == "PUBLISHED_NO_ARTWORK"
    ]
    ep36_anomaly = next(
        (a for a in no_art_anomalies if a.episode_id == "ep_0036"), None
    )
    assert ep36_anomaly is not None, "ep_0036 should be flagged as published with no artwork"


@pytest.mark.asyncio
async def test_seed_detects_casing_anomalies(db):
    """ep_0071 (ALL-CAPS) and ep_0078 (all-lowercase) are flagged."""
    result = await import_seed_file(db, SEED_PATH)

    caps_anomalies = [a for a in result.anomalies if a.anomaly_type == "TITLE_ALL_CAPS"]
    lower_anomalies = [a for a in result.anomalies if a.anomaly_type == "TITLE_ALL_LOWERCASE"]

    assert any(a.episode_id == "ep_0071" for a in caps_anomalies), \
        "ep_0071 ALL-CAPS title not flagged"
    assert any(a.episode_id == "ep_0078" for a in lower_anomalies), \
        "ep_0078 all-lowercase title not flagged"


@pytest.mark.asyncio
async def test_seed_preserves_draft_status(db):
    """Draft episodes remain draft — not promoted."""
    await import_seed_file(db, SEED_PATH)

    draft_eps = await db.execute(
        select(Episode).where(Episode.status == "draft")
    )
    draft_list = list(draft_eps.scalars().all())
    # ep_0083, ep_0084 (Number Nest), and all 8 Rhyme Rangers = 10 draft eps
    assert len(draft_list) == 10, f"Expected 10 draft episodes, got {len(draft_list)}"


@pytest.mark.asyncio
async def test_seed_preserves_season_zero(db):
    """Season 0 trailer records exist and are not modified."""
    await import_seed_file(db, SEED_PATH)

    trailers = await db.execute(
        select(Episode).where(Episode.season_id.in_(
            select(Season.id).where(Season.season_number == 0)
        ))
    )
    trailer_list = list(trailers.scalars().all())
    # ep_0093 and ep_0094
    assert len(trailer_list) == 2, f"Expected 2 trailer episodes, got {len(trailer_list)}"
    for t in trailer_list:
        assert t.duration_seconds == 75


@pytest.mark.asyncio
async def test_seed_idempotent(db):
    """Running seed twice does not create duplicate shows/episodes."""
    await import_seed_file(db, SEED_PATH)
    result2 = await import_seed_file(db, SEED_PATH)

    # All episodes should be skipped on second run
    assert result2.episodes_created == 0
    assert result2.episodes_skipped == 95

    # Show count should still be 8
    count = await db.execute(select(func.count(Show.id)))
    assert count.scalar_one() == 8


@pytest.mark.asyncio
async def test_seed_preserves_ep9001_id(db):
    """ep_9001 should exist in the DB with its original title preserved."""
    await import_seed_file(db, SEED_PATH)

    ep = await db.execute(
        select(Episode).where(Episode.external_id == "ep_9001")
    )
    ep9001 = ep.scalar_one_or_none()
    assert ep9001 is not None, "ep_9001 should be in the DB"
    assert ep9001.title == "The Lost Kite (v2)", "ep_9001 title should be preserved as-is"
    assert ep9001.language == "hi"
    assert ep9001.content_group == "motis-many-lives-s01e02"
