"""Season CRUD endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_editor
from app.database import get_db
from app.models import Season, Show, User
from app.schemas import SeasonCreate, SeasonOut

router = APIRouter(prefix="/shows/{show_id}/seasons", tags=["seasons"])


@router.get("", response_model=list[SeasonOut])
async def list_seasons(
    show_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    # Verify show exists
    show_result = await db.execute(select(Show).where(Show.id == show_id))
    if show_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Show not found.")

    result = await db.execute(
        select(Season).where(Season.show_id == show_id).order_by(Season.season_number)
    )
    return list(result.scalars().all())


@router.post("", response_model=SeasonOut, status_code=status.HTTP_201_CREATED)
async def create_season(
    show_id: uuid.UUID,
    body: SeasonCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    show_result = await db.execute(select(Show).where(Show.id == show_id))
    if show_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Show not found.")

    existing = await db.execute(
        select(Season).where(
            Season.show_id == show_id, Season.season_number == body.season_number
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Season {body.season_number} already exists for this show.",
        )

    season = Season(show_id=show_id, season_number=body.season_number)
    db.add(season)
    await db.flush()
    return season


@router.delete("/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_season(
    show_id: uuid.UUID,
    season_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    result = await db.execute(
        select(Season).where(Season.id == season_id, Season.show_id == show_id)
    )
    season = result.scalar_one_or_none()
    if season is None:
        raise HTTPException(status_code=404, detail="Season not found.")
    await db.delete(season)
    await db.commit()
