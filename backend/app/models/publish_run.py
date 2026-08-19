"""
PublishRun model — append-only audit record for each catalogue publish attempt.

The run record is the sentinel for atomic publish:
  - created with status='running' before writing the catalogue file
  - updated to 'success' or 'failed' after the atomic swap completes
  - a stuck 'running' run after N minutes indicates a crashed publish job
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PublishRun(Base):
    __tablename__ = "publish_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    triggered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # "running" | "success" | "failed"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running", index=True
    )

    shows_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episodes_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Error message if status='failed'
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Object-store key of the written catalogue file
    catalog_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    triggered_by_user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="publish_runs", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<PublishRun {self.id} status={self.status!r}>"
