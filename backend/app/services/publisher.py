"""
Publisher service — atomic catalogue write with run record.

Atomicity strategy:
1. Create publish_run record with status='running'
2. Build catalogue JSON in memory
3. Write to storage as catalog_<run_id>.json (temporary key)
4. Atomic rename → catalog.json (os.replace on local; copy+delete on S3)
5. Update publish_run → status='success'

If process dies at step 3: catalog.json is untouched; run stays 'running'
If process dies at step 4: same as above
If process dies at step 5: catalog.json is updated; run stays 'running' (monitoring catches this)
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Episode, PublishRun, Show
from app.services.artwork_storage import get_storage
from app.services.catalog_builder import build_catalog
from app.services.validator import build_validation_report


CATALOG_KEY = "catalog.json"


async def run_publish(db: AsyncSession, triggered_by: uuid.UUID) -> PublishRun:
    """
    Run the full publish pipeline atomically.
    Returns the completed PublishRun record.
    Raises ValueError if there are blocking validation errors.
    """
    # ── 0. Check no publish already running ────────────────────────────────
    running = await db.execute(
        select(PublishRun).where(PublishRun.status == "running")
    )
    if running.scalar_one_or_none() is not None:
        raise ValueError(
            "A publish job is already running. Wait for it to finish or "
            "investigate if it appears stuck."
        )

    # ── 1. Validate — fail fast if blocking issues exist ───────────────────
    report = await build_validation_report(db)
    if not report.can_publish:
        raise ValueError(
            f"Cannot publish: {report.summary['blocking']} blocking issue(s) found. "
            "Resolve them in the CMS and try again."
        )

    # ── 2. Create run record (sentinel) ────────────────────────────────────
    run = PublishRun(
        triggered_by=triggered_by,
        status="running",
    )
    db.add(run)
    await db.flush()  # get the id

    try:
        # ── 3. Build catalogue in memory ───────────────────────────────────
        catalog = await build_catalog(db, run.id)

        # Count published shows / episodes (regular + trailers)
        shows_count = sum(len(s) for s in catalog.sections.values())
        episodes_count = sum(
            len(season.episodes)
            for shows in catalog.sections.values()
            for show in shows
            for season in show.seasons
        ) + sum(
            len(show.trailers)
            for shows in catalog.sections.values()
            for show in shows
        )

        # ── 4. Write to temporary key ──────────────────────────────────────
        storage = get_storage()
        tmp_key = f"catalog_{run.id}.json"
        catalog_json = catalog.model_dump_json(indent=2)
        await storage.put(tmp_key, catalog_json.encode(), "application/json")

        # ── 5. Atomic swap: tmp_key → catalog.json ─────────────────────────
        await storage.atomic_replace(tmp_key, CATALOG_KEY)

        # ── 6. Update run record ───────────────────────────────────────────
        run.status = "success"
        run.finished_at = datetime.now(timezone.utc)
        run.shows_count = shows_count
        run.episodes_count = episodes_count
        run.catalog_key = CATALOG_KEY

        await db.flush()
        return run

    except Exception as exc:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = str(exc)
        await db.flush()
        raise
