"""Season model — a season belongs to one show."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("show_id", "season_number", name="uq_seasons_show_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    show_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Season 0 is the designated trailer season (reference.json convention).
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    show: Mapped["Show"] = relationship(back_populates="seasons", lazy="noload")  # noqa: F821
    episodes: Mapped[list["Episode"]] = relationship(  # noqa: F821
        back_populates="season",
        cascade="all, delete-orphan",
        order_by="Episode.episode_number",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Season show_id={self.show_id} number={self.season_number}>"
