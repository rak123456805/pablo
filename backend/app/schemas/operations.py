"""Artwork and PublishRun Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


# ─────────────────────────────────────────────────────────────────────────────
# Artwork
# ─────────────────────────────────────────────────────────────────────────────

class ArtworkOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    owner_type: str
    owner_id: uuid.UUID
    kind: str
    storage_key: str
    size_bytes: int
    width_px: int
    height_px: int
    content_type: str
    created_at: datetime
    url: str | None = None  # populated by API layer from storage backend


# ─────────────────────────────────────────────────────────────────────────────
# Publish runs
# ─────────────────────────────────────────────────────────────────────────────

class PublishRunOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    triggered_by: uuid.UUID | None
    started_at: datetime
    finished_at: datetime | None
    status: str
    shows_count: int | None
    episodes_count: int | None
    error_message: str | None
    catalog_key: str | None


class PublishRunListOut(BaseModel):
    items: list[PublishRunOut]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# Validation report
# ─────────────────────────────────────────────────────────────────────────────

class ValidationIssue(BaseModel):
    # Structured fields — allow frontend to link issues to specific records
    entity: str | None = None          # "show" | "episode" | "season"
    entity_id: str | None = None       # UUID or external_id string
    field: str | None = None           # "section" | "artwork" | "duration" | ...
    code: str
    severity: Literal["blocking", "warning", "info"]
    message: str


class ShowValidationEntry(BaseModel):
    show_id: uuid.UUID
    show_title: str
    slug: str
    issues: list[ValidationIssue]


class EpisodeValidationEntry(BaseModel):
    show_id: uuid.UUID
    show_title: str
    slug: str
    episode_id: uuid.UUID
    episode_title: str
    season_number: int
    episode_number: int
    language: str
    content_group: str
    issues: list[ValidationIssue]


class ValidationReport(BaseModel):
    generated_at: datetime
    can_publish: bool
    show_issues: list[ShowValidationEntry]
    episode_issues: list[EpisodeValidationEntry]
    summary: dict[str, int]  # {"blocking": N, "warning": N, "info": N}


# ─────────────────────────────────────────────────────────────────────────────
# Catalogue / viewer
# ─────────────────────────────────────────────────────────────────────────────

class CatalogEpisodeEntry(BaseModel):
    content_group: str
    episode_number: int
    title: str
    languages: list[str]
    duration_seconds: int | None
    artwork: dict[str, str]  # kind -> URL


class CatalogSeasonEntry(BaseModel):
    season_number: int
    episodes: list[CatalogEpisodeEntry]


class CatalogShowEntry(BaseModel):
    slug: str
    title: str
    synopsis: str | None
    section: str
    categories: list[str]
    artwork: dict[str, str]
    seasons: list[CatalogSeasonEntry]
    trailers: list[CatalogEpisodeEntry] = []  # season 0 episodes


class CatalogOut(BaseModel):
    schema_version: str = "1"
    generated_at: str
    publish_run_id: str
    sections: dict[str, list[CatalogShowEntry]]
