"""
Catalogue and search tests — verifies content_group collapse, Season 0 separation,
and search filtering.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from app.models import Artwork, Episode, Season, Show
from app.services.catalog_builder import build_catalog
from app.services.seed_importer import import_seed_file

SEED_PATH = Path(__file__).parent.parent.parent / "seed_shows.json"


@pytest.mark.asyncio
async def test_catalog_builder_structure(db):
    """Test catalogue structure generated from clean published data."""
    import uuid

    # Create show with 2 seasons (Season 0 and Season 1) and bilingual episode
    show = Show(
        slug="jungle-tales",
        title="Jungle Tales",
        synopsis="Fun in the jungle",
        section="series",
        categories=["adventure", "nature"],
        status="published",
    )
    db.add(show)
    await db.flush()

    s0 = Season(show_id=show.id, season_number=0)
    s1 = Season(show_id=show.id, season_number=1)
    db.add_all([s0, s1])
    await db.flush()

    # Season 0 trailer
    ep_trailer = Episode(
        show_id=show.id,
        season_id=s0.id,
        episode_number=1,
        title="Jungle Trailer",
        duration_seconds=60,
        language="en",
        content_group="jungle-tales-s00e01",
        status="published",
    )
    # Season 1 Episode 1 (en and hi variants)
    ep_en = Episode(
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        title="The Big Tree",
        duration_seconds=300,
        language="en",
        content_group="jungle-tales-s01e01",
        status="published",
    )
    ep_hi = Episode(
        show_id=show.id,
        season_id=s1.id,
        episode_number=1,
        title="Bada Ped",
        duration_seconds=300,
        language="hi",
        content_group="jungle-tales-s01e01",
        status="published",
    )
    db.add_all([ep_trailer, ep_en, ep_hi])
    await db.flush()

    # Build catalog
    run_id = uuid.uuid4()
    catalog = await build_catalog(db, run_id)

    # 1. Sections exist
    assert "series" in catalog.sections
    shows = catalog.sections["series"]
    assert len(shows) == 1
    show_entry = shows[0]
    assert show_entry.slug == "jungle-tales"

    # 2. Season 0 is in trailers[], NOT in seasons[]
    assert len(show_entry.trailers) == 1
    assert show_entry.trailers[0].content_group == "jungle-tales-s00e01"
    assert len(show_entry.seasons) == 1
    assert show_entry.seasons[0].season_number == 1

    # 3. Bilingual content_group collapsed to 1 entry with languages=["en", "hi"]
    season_1_eps = show_entry.seasons[0].episodes
    assert len(season_1_eps) == 1
    assert season_1_eps[0].content_group == "jungle-tales-s01e01"
    assert sorted(season_1_eps[0].languages) == ["en", "hi"]
    assert season_1_eps[0].title == "The Big Tree"


@pytest.mark.asyncio
async def test_search_catalog(client, db):
    """Test search endpoint behavior."""
    from app.services.artwork_storage import get_storage
    from app.services.publisher import CATALOG_KEY

    # Write a test catalog to storage
    test_catalog = {
        "schema_version": "1",
        "generated_at": "2026-08-19T00:00:00Z",
        "publish_run_id": "test-run-123",
        "sections": {
            "featured": [
                {
                    "slug": "moti-lives",
                    "title": "Moti's Many Lives",
                    "synopsis": "Stories of Moti",
                    "section": "featured",
                    "categories": ["adventure", "values"],
                    "artwork": {},
                    "seasons": [
                        {
                            "season_number": 1,
                            "episodes": [
                                {
                                    "content_group": "motis-many-lives-s01e01",
                                    "episode_number": 1,
                                    "title": "A New Home",
                                    "languages": ["en", "hi"],
                                    "duration_seconds": 240,
                                    "artwork": {},
                                }
                            ],
                        }
                    ],
                    "trailers": [],
                }
            ],
            "series": [],
            "minisodes": [],
            "songs": [],
        },
    }
    storage = get_storage()
    import json
    await storage.put(CATALOG_KEY, json.dumps(test_catalog).encode(), "application/json")

    # 1. Fetch entire catalog
    resp = await client.get("/api/v1/catalog")
    assert resp.status_code == 200
    assert resp.json()["publish_run_id"] == "test-run-123"

    # 2. Search query match
    resp = await client.get("/api/v1/catalog/search?q=Moti")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["title"] == "Moti's Many Lives"

    # 3. Filter by category
    resp = await client.get("/api/v1/catalog/search?category=values")
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1

    # 4. Filter by non-existent category
    resp = await client.get("/api/v1/catalog/search?category=science")
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 0

    # 5. Filter by language
    resp = await client.get("/api/v1/catalog/search?language=hi")
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1
