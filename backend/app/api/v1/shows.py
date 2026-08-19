"""Shows CRUD endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_editor
from app.database import get_db
from app.models import Show, User
from app.reference import SECTIONS
from app.schemas import ShowCreate, ShowListOut, ShowOut, ShowUpdate

router = APIRouter(prefix="/shows", tags=["shows"])


def _assert_publish_ready(title: str, section: str | None, new_status: str | None) -> None:
    """Raise HTTP 422 if the show violates a publish-time requirement."""
    if new_status == "published":
        if section is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Cannot publish '{title}' because it has no section assigned. "
                    "Please choose a section (featured / series / minisodes / songs) first."
                ),
            )


@router.get("", response_model=ShowListOut)
async def list_shows(
    section: str | None = Query(None),
    show_status: str | None = Query(None, alias="status"),
    q: str | None = Query(None, description="Search by title"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    query = select(Show)
    if section:
        query = query.where(Show.section == section)
    if show_status:
        query = query.where(Show.status == show_status)
    if q:
        query = query.where(Show.title.ilike(f"%{q}%"))

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    query = query.order_by(Show.title).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    shows = result.scalars().all()

    return ShowListOut(items=list(shows), total=total, page=page, page_size=page_size)


@router.post("", response_model=ShowOut, status_code=status.HTTP_201_CREATED)
async def create_show(
    body: ShowCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    existing = await db.execute(select(Show).where(Show.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Show with slug '{body.slug}' already exists.")

    # Enforce: published show requires section
    _assert_publish_ready(body.title, body.section, body.status)

    show = Show(**body.model_dump())
    db.add(show)
    await db.flush()
    return show


@router.get("/{show_id}", response_model=ShowOut)
async def get_show(
    show_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if show is None:
        raise HTTPException(status_code=404, detail="Show not found.")
    return show


@router.patch("/{show_id}", response_model=ShowOut)
async def update_show(
    show_id: uuid.UUID,
    body: ShowUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if show is None:
        raise HTTPException(status_code=404, detail="Show not found.")

    update_data = body.model_dump(exclude_unset=True)

    # Enforce: published show requires section
    # Compute effective values after applying the patch
    effective_section = update_data.get("section", show.section)
    effective_status = update_data.get("status", show.status)
    _assert_publish_ready(show.title, effective_section, effective_status)

    for field, value in update_data.items():
        setattr(show, field, value)

    await db.flush()
    return show


@router.delete("/{show_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_show(
    show_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if show is None:
        raise HTTPException(status_code=404, detail="Show not found.")
    await db.delete(show)
