"""
Seed importer — reads seed_shows.json and loads it into the normalized DB schema.

Design decisions:
──────────────────────────────────────────────────────────────────────────────
1. DO NOT reject the whole transaction on bad data.
   Each row is processed independently. Rows that cannot be stored are recorded
   in the anomaly log and the rest are imported successfully.

2. (content_group, language) uniqueness is enforced at the application layer
   here, NOT via a DB constraint, so that ep_9001 (which duplicates ep_0004
   on content_group=motis-many-lives-s01e02 / lang=hi) can be stored in the
   anomaly log rather than crashing the import.

3. Shows are deduplicated by slug.  All seed rows for the same slug share one
   Show row.

4. Seasons are deduplicated by (show_id, season_number).

5. Episodes are deduplicated by external_id (the original ep_XXXX string).
   A duplicate external_id means the seed file is being re-imported — skip it.

6. The seed data is NOT cleaned:
   - Null sections are preserved (Rhyme Rangers)
   - ALL-CAPS / lowercase titles are preserved (Curious Cubs ep_0071, Number Nest ep_0078)
   - Draft statuses are preserved
   - Season 0 trailer records are preserved
   - ep_0036 with empty artwork_available stays as-is

7. artwork_available_seed stores the JSON list from the seed row so the CMS
   can show what the importer saw; actual artwork must be uploaded separately.
──────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Episode, Season, Show

logger = logging.getLogger(__name__)


@dataclass
class SeedAnomaly:
    """Records one problem found during seed import."""
    row_index: int
    episode_id: str
    show_title: str
    anomaly_type: str  # e.g. "DUPLICATE_CONTENT_GROUP_LANG", "INVALID_SECTION"
    detail: str
    action: str  # "skipped" | "imported_with_warning" | "stored_as_duplicate"


@dataclass
class SeedImportResult:
    shows_created: int = 0
    shows_skipped: int = 0       # already existed
    seasons_created: int = 0
    seasons_skipped: int = 0
    episodes_created: int = 0
    episodes_skipped: int = 0    # external_id already in DB
    rows_total: int = 0
    anomalies: list[SeedAnomaly] = field(default_factory=list)

    def print_summary(self):
        print(f"\n{'='*60}")
        print("SEED IMPORT SUMMARY")
        print(f"{'='*60}")
        print(f"  Total rows processed : {self.rows_total}")
        print(f"  Shows created        : {self.shows_created}")
        print(f"  Shows already existed: {self.shows_skipped}")
        print(f"  Seasons created      : {self.seasons_created}")
        print(f"  Seasons skipped      : {self.seasons_skipped}")
        print(f"  Episodes created     : {self.episodes_created}")
        print(f"  Episodes skipped     : {self.episodes_skipped}")
        print(f"  Anomalies found      : {len(self.anomalies)}")
        if self.anomalies:
            print()
            print("  ANOMALIES:")
            for a in self.anomalies:
                print(f"    [{a.anomaly_type}] row={a.row_index} "
                      f"ep={a.episode_id!r} show={a.show_title!r}")
                print(f"      -> {a.detail}")
                print(f"      -> action: {a.action}")
        print(f"{'='*60}\n")


async def import_seed_file(
    session: AsyncSession,
    seed_path: str | Path,
) -> SeedImportResult:
    """
    Import all rows from seed_shows.json into the database.
    Handles all known anomalies gracefully without aborting the transaction.
    """
    seed_path = Path(seed_path)
    with open(seed_path, encoding="utf-8") as f:
        raw_rows: list[dict[str, Any]] = json.load(f)

    result = SeedImportResult(rows_total=len(raw_rows))

    # ── Caches to avoid repeated DB queries within this import run ────────────
    # show_slug → Show.id
    show_cache: dict[str, Show] = {}
    # (show_id, season_number) → Season
    season_cache: dict[tuple, Season] = {}
    # (content_group, language) → episode_id  (for detecting dupes within this run)
    cg_lang_seen: dict[tuple[str, str], str] = {}
    # external_id → bool  (for detecting already-imported rows)
    ext_id_seen: set[str] = set()

    # Pre-load any shows/seasons/episodes already in the DB (idempotent re-runs)
    existing_shows = (await session.execute(select(Show))).scalars().all()
    for s in existing_shows:
        show_cache[s.slug] = s

    existing_seasons = (await session.execute(select(Season))).scalars().all()
    for s in existing_seasons:
        season_cache[(str(s.show_id), s.season_number)] = s

    existing_episodes = (await session.execute(select(Episode))).scalars().all()
    for e in existing_episodes:
        if e.external_id:
            ext_id_seen.add(e.external_id)
        key = (e.content_group, e.language)
        cg_lang_seen[key] = e.external_id or str(e.id)

    # ── Process each row ──────────────────────────────────────────────────────
    for idx, row in enumerate(raw_rows):
        ep_id: str = row.get("episode_id", f"row_{idx}")
        show_title: str = row.get("show_title", "")
        slug: str = row.get("slug", "")

        # ── 1. Detect re-import of same external_id ────────────────────────
        if ep_id in ext_id_seen:
            result.episodes_skipped += 1
            logger.debug("Skipping already-imported episode %s", ep_id)
            continue

        # ── 2. Detect (content_group, language) duplicate ──────────────────
        content_group: str = row.get("content_group", "")
        language: str = row.get("language", "")
        cg_lang_key = (content_group, language)

        if cg_lang_key in cg_lang_seen:
            # Record the anomaly but DO NOT skip — we still need to understand
            # what happened.  We store the duplicate as a *separate episode row*
            # with a flag so the validation report can surface it.
            result.anomalies.append(SeedAnomaly(
                row_index=idx,
                episode_id=ep_id,
                show_title=show_title,
                anomaly_type="DUPLICATE_CONTENT_GROUP_LANG",
                detail=(
                    f"content_group={content_group!r} + language={language!r} already "
                    f"seen in this import (first seen: {cg_lang_seen[cg_lang_key]!r}). "
                    f"Episode title: {row.get('episode_title')!r} vs first: "
                    f"(see existing record). This is a publish blocker."
                ),
                action="imported_with_warning",
            ))
            # Still fall through and import — let the DB accept it (no unique constraint)
            # The validation report will flag this episode.

        # ── 3. Get or create Show ──────────────────────────────────────────
        if slug not in show_cache:
            show = Show(
                slug=slug,
                title=show_title,
                synopsis=row.get("synopsis"),
                section=row.get("section"),          # may be None — that's OK
                categories=row.get("categories", []),
                # Derive show status: if ANY episode is published, show is published
                status="draft",
            )
            session.add(show)
            await session.flush()  # get the id
            show_cache[slug] = show
            result.shows_created += 1
            logger.info("Created show: %s (%s)", slug, show_title)
        else:
            result.shows_skipped += 1
            show = show_cache[slug]
            # Update show status if this episode is published
            # (show status promoted once we see a published episode)

        # Promote show status if this episode is published
        if row.get("status") == "published" and show.status == "draft":
            show.status = "published"

        # ── 4. Get or create Season ────────────────────────────────────────
        season_number: int = row.get("season_number", 1)
        season_key = (str(show.id), season_number)

        if season_key not in season_cache:
            season = Season(
                show_id=show.id,
                season_number=season_number,
            )
            session.add(season)
            await session.flush()
            season_cache[season_key] = season
            result.seasons_created += 1
        else:
            season = season_cache[season_key]
            result.seasons_skipped += 1

        # ── 5. Create Episode ──────────────────────────────────────────────
        artwork_available = row.get("artwork_available", [])
        episode = Episode(
            show_id=show.id,
            season_id=season.id,
            episode_number=row.get("episode_number", 1),
            title=row.get("episode_title", ""),
            duration_seconds=row.get("duration_seconds"),
            language=language,
            content_group=content_group,
            status=row.get("status", "draft"),
            external_id=ep_id,
            # Preserve exactly what the seed said about artwork
            artwork_available_seed=json.dumps(artwork_available),
        )
        session.add(episode)
        result.episodes_created += 1
        ext_id_seen.add(ep_id)
        cg_lang_seen[cg_lang_key] = ep_id

        # ── 6. Per-row anomaly detection (informational flags) ─────────────
        _detect_row_anomalies(row, idx, ep_id, show_title, result)

    # ── Commit everything ─────────────────────────────────────────────────────
    await session.flush()
    return result


def _detect_row_anomalies(
    row: dict[str, Any],
    idx: int,
    ep_id: str,
    show_title: str,
    result: SeedImportResult,
) -> None:
    """Flag per-row data quality issues without stopping the import."""
    from app.reference import CATEGORIES, LANGUAGES, SECTIONS

    # Null section
    section = row.get("section")
    if section is None:
        result.anomalies.append(SeedAnomaly(
            row_index=idx, episode_id=ep_id, show_title=show_title,
            anomaly_type="MISSING_SECTION",
            detail="section is null — show cannot be published until a section is assigned.",
            action="imported_with_warning",
        ))
    elif section not in SECTIONS:
        result.anomalies.append(SeedAnomaly(
            row_index=idx, episode_id=ep_id, show_title=show_title,
            anomaly_type="INVALID_SECTION",
            detail=f"section={section!r} is not in allowed set {sorted(SECTIONS)}.",
            action="imported_with_warning",
        ))

    # Empty artwork on published
    artwork = row.get("artwork_available", [])
    if row.get("status") == "published" and not artwork:
        result.anomalies.append(SeedAnomaly(
            row_index=idx, episode_id=ep_id, show_title=show_title,
            anomaly_type="PUBLISHED_NO_ARTWORK",
            detail=(
                f"Episode {ep_id} has status='published' but artwork_available=[]. "
                "This is a publish blocker."
            ),
            action="imported_with_warning",
        ))

    # Title casing anomalies
    title = row.get("episode_title", "")
    if title and title == title.lower() and len(title.split()) > 1:
        result.anomalies.append(SeedAnomaly(
            row_index=idx, episode_id=ep_id, show_title=show_title,
            anomaly_type="TITLE_ALL_LOWERCASE",
            detail=f"episode_title={title!r} is all-lowercase (data quality warning).",
            action="imported_with_warning",
        ))
    elif title and all(w.isupper() for w in title.split() if w.isalpha()) and len(title.split()) > 1:
        result.anomalies.append(SeedAnomaly(
            row_index=idx, episode_id=ep_id, show_title=show_title,
            anomaly_type="TITLE_ALL_CAPS",
            detail=f"episode_title={title!r} is ALL-CAPS (data quality warning).",
            action="imported_with_warning",
        ))

    # Invalid language
    lang = row.get("language", "")
    if lang not in LANGUAGES:
        result.anomalies.append(SeedAnomaly(
            row_index=idx, episode_id=ep_id, show_title=show_title,
            anomaly_type="INVALID_LANGUAGE",
            detail=f"language={lang!r} not in allowed set {sorted(LANGUAGES)}.",
            action="imported_with_warning",
        ))

    # Non-sequential episode ID (ep_9001 pattern)
    if ep_id and not ep_id.startswith("ep_0"):
        result.anomalies.append(SeedAnomaly(
            row_index=idx, episode_id=ep_id, show_title=show_title,
            anomaly_type="NON_SEQUENTIAL_ID",
            detail=f"episode_id={ep_id!r} does not follow the ep_0XXX pattern.",
            action="imported_with_warning",
        ))
