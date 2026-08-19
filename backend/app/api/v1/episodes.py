"""Episode CRUD endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_editor
from app.database import get_db
from app.models import Episode, Season, User
from app.schemas import EpisodeCreate, EpisodeListOut, EpisodeOut, EpisodeUpdate

router = APIRouter(prefix="/episodes", tags=["episodes"])


def _assert_episode_publish_ready(
    title: str,
    duration_seconds: int | None,
    new_status: str | None,
) -> None:
    """Raise HTTP 422 if the episode violates publish-time requirements."""
    if new_status == "published":
        if duration_seconds is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Cannot publish episode '{title}' because it has no duration set. "
                    "Please add a duration in seconds before publishing."
                ),
            )


@router.get("", response_model=EpisodeListOut)
async def list_episodes(
    show_id: uuid.UUID | None = Query(None),
    season_id: uuid.UUID | None = Query(None),
    ep_status: str | None = Query(None, alias="status"),
    language: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    query = select(Episode)
    if show_id:
        query = query.where(Episode.show_id == show_id)
    if season_id:
        query = query.where(Episode.season_id == season_id)
    if ep_status:
        query = query.where(Episode.status == ep_status)
    if language:
        query = query.where(Episode.language == language)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    query = (
        query.order_by(Episode.episode_number)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    episodes = result.scalars().all()

    return EpisodeListOut(items=list(episodes), total=total, page=page, page_size=page_size)


@router.post("", response_model=EpisodeOut, status_code=status.HTTP_201_CREATED)
async def create_episode(
    body: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    # Verify season exists and get show_id
    season_result = await db.execute(select(Season).where(Season.id == body.season_id))
    season = season_result.scalar_one_or_none()
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found.")

    # Enforce (content_group, language) uniqueness at app layer
    existing = await db.execute(
        select(Episode).where(
            Episode.content_group == body.content_group,
            Episode.language == body.language,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"An episode with content_group='{body.content_group}' and "
                f"language='{body.language}' already exists. "
                "Each (content_group, language) pair must be unique."
            ),
        )

    # Enforce: published episode requires duration
    _assert_episode_publish_ready(body.title, body.duration_seconds, body.status)

    episode = Episode(
        show_id=season.show_id,
        season_id=body.season_id,
        episode_number=body.episode_number,
        title=body.title,
        duration_seconds=body.duration_seconds,
        language=body.language,
        content_group=body.content_group,
        status=body.status,
    )
    db.add(episode)
    await db.flush()
    return episode


@router.get("/{episode_id}", response_model=EpisodeOut)
async def get_episode(
    episode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found.")
    return episode


@router.patch("/{episode_id}", response_model=EpisodeOut)
async def update_episode(
    episode_id: uuid.UUID,
    body: EpisodeUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found.")

    update_data = body.model_dump(exclude_unset=True)

    # Check (content_group, language) uniqueness if either is being updated
    new_cg = update_data.get("content_group", episode.content_group)
    new_lang = update_data.get("language", episode.language)
    if new_cg != episode.content_group or new_lang != episode.language:
        conflict = await db.execute(
            select(Episode).where(
                Episode.content_group == new_cg,
                Episode.language == new_lang,
                Episode.id != episode_id,
            )
        )
        if conflict.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"An episode with content_group='{new_cg}' and "
                    f"language='{new_lang}' already exists."
                ),
            )

    # Enforce: published episode requires duration
    effective_duration = update_data.get("duration_seconds", episode.duration_seconds)
    effective_status = update_data.get("status", episode.status)
    effective_title = update_data.get("title", episode.title)
    _assert_episode_publish_ready(effective_title, effective_duration, effective_status)

    for field, value in update_data.items():
        setattr(episode, field, value)

    await db.flush()
    await db.refresh(episode)
    return episode


@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    episode = result.scalar_one_or_none()
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found.")
    await db.delete(episode)
