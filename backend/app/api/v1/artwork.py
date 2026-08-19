"""Artwork upload endpoint."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_editor
from app.core.image_validator import (
    ImageValidationError,
    detected_content_type,
    validate_artwork,
)
from app.database import get_db
from app.models import Artwork, Episode, Show, User
from app.reference import ARTWORK_KINDS
from app.schemas import ArtworkOut
from app.services.artwork_storage import get_storage

router = APIRouter(prefix="/artwork", tags=["artwork"])


@router.post("", response_model=ArtworkOut, status_code=status.HTTP_201_CREATED)
@router.post("s", response_model=ArtworkOut, status_code=status.HTTP_201_CREATED)
async def upload_artwork(
    kind: str = Form(..., description="poster | banner | thumbnail"),
    owner_type: str = Form(..., description="show | episode"),
    owner_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    # Validate kind
    if kind not in ARTWORK_KINDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid artwork kind '{kind}'. Allowed: {sorted(ARTWORK_KINDS)}.",
        )

    # Validate owner_type
    if owner_type not in ("show", "episode"):
        raise HTTPException(
            status_code=400,
            detail="owner_type must be 'show' or 'episode'.",
        )

    # Parse owner_id string as UUID or look up by external_id / slug
    owner_uuid: uuid.UUID | None = None
    try:
        owner_uuid = uuid.UUID(owner_id)
    except ValueError:
        pass

    # Verify owner exists
    if owner_type == "show":
        if owner_uuid:
            result = await db.execute(select(Show).where(Show.id == owner_uuid))
        else:
            result = await db.execute(select(Show).where(Show.slug == owner_id))
        show_obj = result.scalar_one_or_none()
        if show_obj is None:
            raise HTTPException(status_code=404, detail="Show not found.")
        owner_uuid = show_obj.id
    else:
        if owner_uuid:
            result = await db.execute(select(Episode).where(Episode.id == owner_uuid))
        else:
            result = await db.execute(select(Episode).where(Episode.external_id == owner_id))
        ep_obj = result.scalar_one_or_none()
        if ep_obj is None:
            raise HTTPException(status_code=404, detail="Episode not found.")
        owner_uuid = ep_obj.id

    # Read file bytes
    data = await file.read()
    # Detect actual content-type from bytes — never trust the HTTP header alone
    content_type = detected_content_type(data)

    # Validate image dimensions, aspect ratio, size, and actual file format
    try:
        width, height = validate_artwork(data, kind, content_type)
    except ImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Delete existing artwork for this owner+kind (upsert)
    existing = await db.execute(
        select(Artwork).where(
            Artwork.owner_type == owner_type,
            Artwork.owner_id == owner_uuid,
            Artwork.kind == kind,
        )
    )
    existing_art = existing.scalar_one_or_none()

    storage = get_storage()

    if existing_art is not None:
        try:
            await storage.delete(existing_art.storage_key)
        except Exception:
            pass  # Best effort storage cleanup
        await db.delete(existing_art)

    # Save to storage backend (Supabase or Local File Storage)
    art_id = uuid.uuid4()
    extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(content_type, "jpg")
    storage_key = f"{owner_type}s/{owner_uuid}/{kind}.{extension}"

    await storage.put(storage_key, data, content_type)

    artwork = Artwork(
        id=art_id,
        owner_type=owner_type,
        owner_id=owner_uuid,
        kind=kind,
        storage_key=storage_key,
        size_bytes=len(data),
        width_px=width,
        height_px=height,
        content_type=content_type,
    )
    db.add(artwork)
    await db.commit()
    await db.refresh(artwork)

    out = ArtworkOut.model_validate(artwork)
    out.url = storage.public_url(artwork.storage_key)
    return out


@router.delete("/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artwork(
    artwork_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    result = await db.execute(select(Artwork).where(Artwork.id == artwork_id))
    artwork = result.scalar_one_or_none()
    if artwork is None:
        raise HTTPException(status_code=404, detail="Artwork not found.")

    storage = get_storage()
    try:
        await storage.delete(artwork.storage_key)
    except Exception:
        pass  # Best effort

    await db.delete(artwork)
    await db.commit()
