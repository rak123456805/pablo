"""
Validation report tests — verifies each blocking rule fires correctly.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from app.models import Episode, Season, Show
from app.services.seed_importer import import_seed_file
from app.services.validator import build_validation_report

SEED_PATH = Path(__file__).parent.parent.parent / "seed_shows.json"


@pytest.mark.asyncio
async def test_validation_report_has_blocking_issues_after_seed(db):
    """After seeding, there should be blocking issues (Rhyme Rangers null section, ep_0036 no artwork)."""
    await import_seed_file(db, SEED_PATH)
    report = await build_validation_report(db)

    assert report.can_publish is False
    assert report.summary["blocking"] > 0


@pytest.mark.asyncio
async def test_validation_flags_missing_section(db):
    """Rhyme Rangers' null section is a blocking issue."""
    await import_seed_file(db, SEED_PATH)
    report = await build_validation_report(db)

    rhyme_rangers_issues = [
        e for e in report.show_issues if e.slug == "rhyme-rangers"
    ]
    assert len(rhyme_rangers_issues) > 0

    codes = [i.code for e in rhyme_rangers_issues for i in e.issues]
    assert "MISSING_SECTION" in codes


@pytest.mark.asyncio
async def test_validation_flags_duplicate_content_group(db):
    """The ep_9001 / ep_0004 duplicate triggers DUPLICATE_CONTENT_GROUP_LANG."""
    await import_seed_file(db, SEED_PATH)
    report = await build_validation_report(db)

    dupe_issues = [
        e for e in report.episode_issues
        if any(i.code == "DUPLICATE_CONTENT_GROUP_LANG" for i in e.issues)
    ]
    assert len(dupe_issues) >= 2  # Both episodes flagged


@pytest.mark.asyncio
async def test_validation_flags_published_without_artwork(db):
    """ep_0036 (Discover India S1E4) is published with no artwork — blocking."""
    await import_seed_file(db, SEED_PATH)
    report = await build_validation_report(db)

    ep36_issues = [
        e for e in report.episode_issues
        if e.content_group == "discover-india-with-moti-s01e04"
    ]
    assert any(
        any(i.code == "MISSING_ARTWORK" for i in e.issues)
        for e in ep36_issues
    ), "ep_0036 MISSING_ARTWORK not reported"


@pytest.mark.asyncio
async def test_validation_flags_casing_warnings(db):
    """Title casing anomalies are surfaced as warnings."""
    await import_seed_file(db, SEED_PATH)
    report = await build_validation_report(db)

    caps_issues = [
        e for e in report.episode_issues
        if any(i.code == "TITLE_ALL_CAPS" for i in e.issues)
    ]
    lower_issues = [
        e for e in report.episode_issues
        if any(i.code == "TITLE_ALL_LOWERCASE" for i in e.issues)
    ]

    assert len(caps_issues) >= 1, "No ALL_CAPS warning"
    assert len(lower_issues) >= 1, "No all-lowercase warning"
    # These should be warnings, not blocking
    for e in caps_issues:
        for i in e.issues:
            if i.code == "TITLE_ALL_CAPS":
                assert i.severity == "warning"


@pytest.mark.asyncio
async def test_clean_show_can_publish(db):
    """A well-formed show with artwork passes validation."""
    from app.models import Artwork

    # Create a clean show, season, episode with artwork
    show = Show(slug="clean-show", title="Clean Show", section="series",
                categories=["stories"], status="published")
    db.add(show)
    await db.flush()

    season = Season(show_id=show.id, season_number=1)
    db.add(season)
    await db.flush()

    ep = Episode(
        show_id=show.id, season_id=season.id, episode_number=1,
        title="Clean Episode", duration_seconds=300, language="en",
        content_group="clean-show-s01e01", status="published",
    )
    db.add(ep)
    await db.flush()

    art = Artwork(
        owner_type="episode", owner_id=ep.id, kind="thumbnail",
        storage_key="episodes/test/thumb.jpg", size_bytes=1000,
        width_px=640, height_px=360, content_type="image/jpeg",
    )
    db.add(art)
    await db.flush()

    report = await build_validation_report(db)
    # The clean episode should not be in blocking issues
    ep_blocks = [
        e for e in report.episode_issues
        if e.episode_id == ep.id
        and any(i.severity == "blocking" for i in e.issues)
    ]
    assert len(ep_blocks) == 0, f"Clean episode should have no blocking issues, got: {ep_blocks}"
