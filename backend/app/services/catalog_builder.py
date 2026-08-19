"""
Catalogue builder — produces the published catalogue JSON structure.

Rules:
  - Only published shows and published episodes are included
  - Season 0 episodes are separated into show.trailers[] (NOT in seasons[])
  - content_group variants collapse into ONE entry with languages: ["en", "hi", ...]
  - Sections appear in reference.json order (deterministic)
  - Shows within a section: alphabetical by title (case-insensitive), UUID as tie-breaker
  - Seasons: ascending by season_number
  - Episodes within a season: ascending by (episode_number, content_group) — stable tie-breaker
  - The same DB state always produces bit-for-bit identical JSON when re-published

Content-group collapsing:
  - English variant is used as the "primary" for title and duration
  - Falls back to whichever variant sorts first alphabetically by language code
  - All languages from the group are included in languages: [...]

Artwork:
  - Show artwork: all kinds for the show owner
  - Episode artwork: taken from the primary language variant's artwork
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Artwork, Episode, Season, Show
from app.reference import SECTIONS
from app.schemas.operations import (
    CatalogEpisodeEntry,
    CatalogOut,
    CatalogSeasonEntry,
    CatalogShowEntry,
)
from app.services.artwork_storage import get_storage


async def build_catalog(
    db: AsyncSession,
    run_id: uuid.UUID,
    generated_at: str | None = None,
) -> CatalogOut:
    """Build the full catalogue JSON from the current published DB state."""
    storage = get_storage()
    timestamp = generated_at or datetime.now(timezone.utc).isoformat()

    # ── Load published shows ──────────────────────────────────────────────────
    shows_result = await db.execute(
        select(Show).where(Show.status == "published")
    )
    published_shows: list[Show] = list(shows_result.scalars().all())

    if not published_shows:
        return CatalogOut(
            generated_at=timestamp,
            publish_run_id=str(run_id),
            sections={s: [] for s in SECTIONS},
        )

    show_ids = [s.id for s in published_shows]

    # ── Load all seasons for published shows ──────────────────────────────────
    seasons_result = await db.execute(
        select(Season).where(Season.show_id.in_(show_ids))
    )
    all_seasons: list[Season] = list(seasons_result.scalars().all())
    season_by_id: dict[uuid.UUID, Season] = {s.id: s for s in all_seasons}
    seasons_by_show: dict[uuid.UUID, list[Season]] = defaultdict(list)
    for s in all_seasons:
        seasons_by_show[s.show_id].append(s)

    # ── Load published episodes for published shows ────────────────────────────
    episodes_result = await db.execute(
        select(Episode).where(
            Episode.show_id.in_(show_ids),
            Episode.status == "published",
        )
    )
    published_episodes: list[Episode] = list(episodes_result.scalars().all())

    # ── Load all artworks ─────────────────────────────────────────────────────
    all_owner_ids = show_ids + [e.id for e in published_episodes]
    artworks_result = await db.execute(
        select(Artwork).where(Artwork.owner_id.in_(all_owner_ids))
    )
    all_artworks: list[Artwork] = list(artworks_result.scalars().all())

    # Artwork lookup: (owner_type, owner_id) → {kind: public_url}
    artwork_map: dict[tuple, dict[str, str]] = defaultdict(dict)
    for art in all_artworks:
        artwork_map[(art.owner_type, art.owner_id)][art.kind] = storage.public_url(
            art.storage_key
        )

    # ── Group episodes: show_id → season_number → content_group → [Episode] ──
    # Structure allows collapsing language variants in one pass.
    eps_by_show_season_cg: dict[
        uuid.UUID, dict[int, dict[str, list[Episode]]]
    ] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for ep in published_episodes:
        season = season_by_id.get(ep.season_id)
        if season is None:
            continue
        eps_by_show_season_cg[ep.show_id][season.season_number][ep.content_group].append(ep)

    # ── Build sections dict in reference.json section order ───────────────────
    sections_dict: dict[str, list[CatalogShowEntry]] = {s: [] for s in SECTIONS}

    # Deterministic show ordering: title (case-insensitive) then id as tie-breaker
    for show in sorted(published_shows, key=lambda s: (s.title.lower(), str(s.id))):
        if show.section not in SECTIONS:
            # Show without a valid section is excluded from the viewer catalogue.
            # The validator will have surfaced this as a blocking issue.
            continue

        show_artwork = artwork_map.get(("show", show.id), {})
        season_entries: list[CatalogSeasonEntry] = []
        trailer_entries: list[CatalogEpisodeEntry] = []

        # Sort seasons by season_number (ascending)
        show_seasons = sorted(
            seasons_by_show.get(show.id, []), key=lambda s: s.season_number
        )

        for season in show_seasons:
            cg_groups = eps_by_show_season_cg[show.id].get(season.season_number, {})
            episode_entries: list[CatalogEpisodeEntry] = []

            for content_group, eps in cg_groups.items():
                # Collapse language variants into one catalogue entry.
                # Primary: English variant for title/duration (most common viewer language).
                # Fall back to lowest alphabetical language code if no English variant.
                sorted_eps = sorted(eps, key=lambda e: e.language)
                primary = next(
                    (e for e in sorted_eps if e.language == "en"), sorted_eps[0]
                )
                languages = sorted({e.language for e in eps})

                # Episode artwork from the primary variant's artwork record
                ep_artwork = artwork_map.get(("episode", primary.id), {})

                entry = CatalogEpisodeEntry(
                    content_group=content_group,
                    episode_number=primary.episode_number,
                    title=primary.title,
                    languages=languages,
                    duration_seconds=primary.duration_seconds,
                    artwork=ep_artwork,
                )

                if season.season_number == 0:
                    trailer_entries.append(entry)
                else:
                    episode_entries.append(entry)

            if season.season_number != 0:
                # Sort episodes by (episode_number, content_group) — stable ordering
                episode_entries.sort(
                    key=lambda e: (e.episode_number, e.content_group)
                )
                if episode_entries:
                    season_entries.append(CatalogSeasonEntry(
                        season_number=season.season_number,
                        episodes=episode_entries,
                    ))

        # Sort trailers by (episode_number, content_group)
        trailer_entries.sort(key=lambda e: (e.episode_number, e.content_group))

        show_entry = CatalogShowEntry(
            slug=show.slug,
            title=show.title,
            synopsis=show.synopsis,
            section=show.section,
            categories=show.categories or [],
            artwork=show_artwork,
            seasons=season_entries,
            trailers=trailer_entries,
        )
        sections_dict[show.section].append(show_entry)

    return CatalogOut(
        generated_at=timestamp,
        publish_run_id=str(run_id),
        sections=sections_dict,
    )
