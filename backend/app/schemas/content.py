"""
Pydantic schemas for Show, Season and Episode resources.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

from app.reference import CATEGORIES, LANGUAGES, SECTIONS


# ─────────────────────────────────────────────────────────────────────────────
# Show schemas
# ─────────────────────────────────────────────────────────────────────────────

class ShowBase(BaseModel):
    title: str
    synopsis: str | None = None
    section: str | None = None
    categories: list[str] = []
    status: Literal["draft", "published"] = "draft"

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: str | None) -> str | None:
        if v is not None and v not in SECTIONS:
            raise ValueError(f"section must be one of {sorted(SECTIONS)}, got {v!r}")
        return v

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        invalid = [c for c in v if c not in CATEGORIES]
        if invalid:
            raise ValueError(f"Invalid categories: {invalid}. Allowed: {sorted(CATEGORIES)}")
        return v


class ShowCreate(ShowBase):
    slug: str


class ShowUpdate(BaseModel):
    title: str | None = None
    synopsis: str | None = None
    section: str | None = None
    categories: list[str] | None = None
    status: Literal["draft", "published"] | None = None

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: str | None) -> str | None:
        if v is not None and v not in SECTIONS:
            raise ValueError(f"section must be one of {sorted(SECTIONS)}, got {v!r}")
        return v

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            invalid = [c for c in v if c not in CATEGORIES]
            if invalid:
                raise ValueError(f"Invalid categories: {invalid}")
        return v


class ShowOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    slug: str
    title: str
    synopsis: str | None
    section: str | None
    categories: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class ShowListOut(BaseModel):
    model_config = {"from_attributes": True}

    items: list[ShowOut]
    total: int
    page: int
    page_size: int


# ─────────────────────────────────────────────────────────────────────────────
# Season schemas
# ─────────────────────────────────────────────────────────────────────────────

class SeasonCreate(BaseModel):
    season_number: int

    @field_validator("season_number")
    @classmethod
    def validate_season_number(cls, v: int) -> int:
        if v < 0:
            raise ValueError("season_number must be >= 0 (0 = trailers)")
        return v


class SeasonOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    show_id: uuid.UUID
    season_number: int
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Episode schemas
# ─────────────────────────────────────────────────────────────────────────────

class EpisodeBase(BaseModel):
    episode_number: int
    title: str
    duration_seconds: int | None = None
    language: str
    content_group: str
    status: Literal["draft", "published"] = "draft"

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in LANGUAGES:
            raise ValueError(f"language must be one of {sorted(LANGUAGES)}, got {v!r}")
        return v

    @field_validator("episode_number")
    @classmethod
    def validate_episode_number(cls, v: int) -> int:
        if v < 1:
            raise ValueError("episode_number must be >= 1")
        return v


class EpisodeCreate(EpisodeBase):
    season_id: uuid.UUID


class EpisodeUpdate(BaseModel):
    title: str | None = None
    duration_seconds: int | None = None
    language: str | None = None
    content_group: str | None = None
    status: Literal["draft", "published"] | None = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str | None) -> str | None:
        if v is not None and v not in LANGUAGES:
            raise ValueError(f"language must be one of {sorted(LANGUAGES)}, got {v!r}")
        return v


class EpisodeOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    show_id: uuid.UUID
    season_id: uuid.UUID
    episode_number: int
    title: str
    duration_seconds: int | None
    language: str
    content_group: str
    status: str
    external_id: str | None
    artwork_available_seed: str | None
    created_at: datetime
    updated_at: datetime


class EpisodeListOut(BaseModel):
    model_config = {"from_attributes": True}

    items: list[EpisodeOut]
    total: int
    page: int
    page_size: int
