"""
Episode model.

Design notes on constraints vs. application validation:
─────────────────────────────────────────────────────
The seed data (ep_9001) contains a duplicate (content_group, language) pair that
intentionally conflicts with ep_0004.  We need to represent both rows in the DB so
the CMS can show the conflict in the validation report.

Therefore:
  - There is NO DB UNIQUE constraint on (content_group, language).
  - The UNIQUE constraint is enforced at the APPLICATION layer:
    * On normal CRUD creates/updates the API rejects duplicates.
    * The seed importer detects the conflict, stores the first record, skips
      the duplicate, and records it in the import anomaly log.
  - A DB-level UNIQUE index IS added for `external_id` to prevent re-importing
    the same seed row twice.

`duration_seconds` is nullable: a published episode without a duration is a
  publish blocker surfaced by the validation report, not a DB constraint.

`artwork_available_seed` is a JSON text field that records what the seed file
  claimed was available — actual artwork is tracked via the artworks table.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ────────────────────────────────────────────────────────
    show_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seasons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Episode identity ─────────────────────────────────────────────────────
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Nullable: required for publish but not for storage
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Language validated at app layer against reference.json; stored as text
    language: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # content_group links language variants of the same episode
    content_group: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    # "draft" | "published"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)

    # ── Seed provenance ──────────────────────────────────────────────────────
    # Original ID from seed file (e.g. "ep_0001").  Unique to detect re-imports.
    external_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, unique=True, index=True
    )

    # What the seed file said was available — informational only.
    # Actual artwork tracked in the artworks table.
    artwork_available_seed: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    show: Mapped["Show"] = relationship(back_populates="episodes", lazy="noload")  # noqa: F821
    season: Mapped["Season"] = relationship(back_populates="episodes", lazy="noload")  # noqa: F821
    artworks: Mapped[list["Artwork"]] = relationship(  # noqa: F821
        primaryjoin="and_(Artwork.owner_type=='episode', foreign(Artwork.owner_id)==Episode.id)",
        lazy="noload",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Episode {self.external_id or self.id} "
            f"cg={self.content_group!r} lang={self.language!r} "
            f"s={self.season_id} e={self.episode_number}>"
        )
