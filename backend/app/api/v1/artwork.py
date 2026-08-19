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
    detected_extension,
    validate_artwork,
)
from app.database import get_db
from app.models import Artwork, Episode, Show, User
from app.reference import ARTWORK_KINDS
from app.schemas import ArtworkOut
from app.services.artwork_storage import get_storage

router = APIRouter(prefix="/artwork", tags=["artwork"])


@router.post("", response_model=ArtworkOut, status_code=status.HTTP_201_CREATED)
async def upload_artwork(
    kind: str = Form(..., description="poster | banner | thumbnail"),
    owner_type: str = Form(..., description="show | episode"),
    owner_id: uuid.UUID = Form(...),
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

    # Verify owner exists
    if owner_type == "show":
        result = await db.execute(select(Show).where(Show.id == owner_id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Show not found.")
    else:
        result = await db.execute(select(Episode).where(Episode.id == owner_id))
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Episode not found.")

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
            Artwork.owner_id == owner_id,
            Artwork.kind == kind,
        )
    )
    existing_art = existing.scalar_one_or_none()

    storage = get_storage()

    # Build storage key using actual extension detected from bytes
    storage_key = f"{owner_type}s/{owner_id}/{kind}.{detected_extension(data)}"

    # Upload to storage
    await storage.put(storage_key, data, content_type)

    if existing_art:
        # Remove old file if key changed
        if existing_art.storage_key != storage_key:
            await storage.delete(existing_art.storage_key)
        # Update record
        existing_art.storage_key = storage_key
        existing_art.size_bytes = len(data)
        existing_art.width_px = width
        existing_art.height_px = height
        existing_art.content_type = content_type
        artwork = existing_art
    else:
        artwork = Artwork(
            owner_type=owner_type,
            owner_id=owner_id,
            kind=kind,
            storage_key=storage_key,
            size_bytes=len(data),
            width_px=width,
            height_px=height,
            content_type=content_type,
        )
        db.add(artwork)

    await db.flush()

    # Build response with URL
    out = ArtworkOut.model_validate(artwork)
    out.url = storage.public_url(storage_key)
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
    await storage.delete(artwork.storage_key)
    await db.delete(artwork)


# _ext() removed — replaced by detected_extension() from image_validator.
