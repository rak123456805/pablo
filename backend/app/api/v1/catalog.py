"""
Catalogue endpoints:
  GET  /catalog               — serve the published catalogue (public)
  GET  /catalog/search        — composable search/filter (public)
  POST /admin/catalog/publish — trigger publish job (admin only)
  GET  /admin/catalog/runs    — publish run history (editor+)
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, require_editor
from app.database import get_db
from app.models import PublishRun, User
from app.schemas import PublishRunListOut, PublishRunOut
from app.services.artwork_storage import get_storage
from app.services.publisher import CATALOG_KEY, run_publish

router = APIRouter(tags=["catalog"])
admin_router = APIRouter(prefix="/admin/catalog", tags=["catalog-admin"])


@router.get("/catalog")
async def get_catalog():
    """Serve the latest published catalogue JSON."""
    storage = get_storage()
    if not storage.exists(CATALOG_KEY):
        raise HTTPException(
            status_code=404,
            detail="No catalogue has been published yet. Trigger a publish run from the CMS.",
        )
    data = await storage.get(CATALOG_KEY)
    return json.loads(data)


@router.get("/catalog/search")
async def search_catalog(
    q: str | None = Query(None, description="Search show title, episode title, categories"),
    category: str | None = Query(None),
    language: str | None = Query(None),
    section: str | None = Query(None),
):
    """
    Filter the published catalogue in memory.
    At current catalogue size (~100 episodes) this is fast enough.
    Above ~5,000 episodes this should move to full-text DB search.
    """
    storage = get_storage()
    if not storage.exists(CATALOG_KEY):
        raise HTTPException(status_code=404, detail="No catalogue published yet.")

    data = await storage.get(CATALOG_KEY)
    catalog = json.loads(data)

    results: list[dict] = []

    for sec_name, shows in catalog.get("sections", {}).items():
        if section and sec_name != section:
            continue
        for show in shows:
            # Category filter on show
            if category and category not in show.get("categories", []):
                continue

            q_lower = q.lower() if q else None
            show_title_matches = q_lower and q_lower in show["title"].lower()

            def ep_matches(ep: dict) -> bool:
                """True if the episode passes language and q filters."""
                if language and language not in ep.get("languages", []):
                    return False
                if q_lower:
                    return (
                        show_title_matches
                        or q_lower in ep["title"].lower()
                        or any(q_lower in c for c in show.get("categories", []))
                    )
                return True

            # Match episodes in regular seasons
            matched_seasons = []
            for season in show.get("seasons", []):
                matched_eps = [ep for ep in season.get("episodes", []) if ep_matches(ep)]
                if matched_eps:
                    matched_seasons.append({**season, "episodes": matched_eps})

            # Match trailers (season 0 episodes)
            matched_trailers = [
                ep for ep in show.get("trailers", []) if ep_matches(ep)
            ]

            # If show title matches q, include all its seasons/trailers
            if show_title_matches and not matched_seasons and not matched_trailers:
                if not language:
                    matched_seasons = show.get("seasons", [])
                    matched_trailers = show.get("trailers", [])
                else:
                    # Still apply language filter even on title match
                    matched_seasons = [
                        {**s, "episodes": [ep for ep in s.get("episodes", []) if ep_matches(ep)]}
                        for s in show.get("seasons", [])
                    ]
                    matched_trailers = [
                        ep for ep in show.get("trailers", []) if ep_matches(ep)
                    ]

            has_content = bool(matched_seasons or matched_trailers)
            # Include the show if it has matching content, or if there are no filters at all
            if has_content or (not q and not language):
                results.append({
                    **show,
                    "seasons": matched_seasons or show.get("seasons", []),
                    "trailers": matched_trailers or show.get("trailers", []),
                    "section": sec_name,
                })

    return {"results": results, "total": len(results)}


@admin_router.post("/publish", response_model=PublishRunOut, status_code=status.HTTP_201_CREATED)
async def publish_catalog(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Trigger an atomic catalogue publish. Admin only."""
    try:
        run = await run_publish(db, triggered_by=user.id)
        return run
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@admin_router.get("/runs", response_model=PublishRunListOut)
async def list_publish_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    total_result = await db.execute(select(func.count(PublishRun.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        select(PublishRun)
        .order_by(desc(PublishRun.started_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    runs = list(result.scalars().all())
    return PublishRunListOut(items=runs, total=total)
