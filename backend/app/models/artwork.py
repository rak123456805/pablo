"""
Artwork model — stores metadata about uploaded image files.

Supports a polymorphic owner: either a Show or an Episode.
One artwork record per (owner_type, owner_id, kind) — enforced by DB UNIQUE.
The actual file bytes live in the storage backend; this table holds metadata.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Artwork(Base):
    __tablename__ = "artworks"
    __table_args__ = (
        UniqueConstraint(
            "owner_type", "owner_id", "kind", name="uq_artworks_owner_kind"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Polymorphic owner reference — "show" or "episode"
    owner_type: Mapped[str] = mapped_column(String(20), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # "poster" | "banner" | "thumbnail"
    kind: Mapped[str] = mapped_column(String(20), nullable=False)

    # Storage backend object key (relative path / object name)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Image metadata
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width_px: Mapped[int] = mapped_column(Integer, nullable=False)
    height_px: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Artwork {self.kind} owner={self.owner_type}:{self.owner_id} "
            f"{self.width_px}x{self.height_px}>"
        )
