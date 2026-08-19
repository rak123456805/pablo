"""
Show model.

Design notes:
- `section` is nullable at the DB level because the seed data contains shows
  (Rhyme Rangers) where section=null.  The DB should accept this so the seed
  importer can load it; the validation-report endpoint surfaces it as a blocker.
- `categories` is stored as a PostgreSQL TEXT ARRAY for O(1) GIN-indexed lookups.
- `status` is scoped per-show (draft | published) separate from episode status.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Nullable: seed data contains shows without a section (Rhyme Rangers).
    # Constraint is at application-validation layer, not DB.
    section: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # PostgreSQL TEXT ARRAY — validated against reference.json at app layer
    categories: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)), nullable=False, default=list
    )

    # "draft" | "published"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    seasons: Mapped[list["Season"]] = relationship(  # noqa: F821
        back_populates="show",
        cascade="all, delete-orphan",
        order_by="Season.season_number",
        lazy="noload",
    )
    episodes: Mapped[list["Episode"]] = relationship(  # noqa: F821
        back_populates="show",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    artworks: Mapped[list["Artwork"]] = relationship(  # noqa: F821
        primaryjoin="and_(Artwork.owner_type=='show', foreign(Artwork.owner_id)==Show.id)",
        lazy="noload",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Show slug={self.slug!r} section={self.section!r}>"
