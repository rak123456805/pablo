"""
Application settings loaded from environment variables via pydantic-settings.
All values have sensible defaults for local development so `docker compose up`
just works; production overrides every variable via environment.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://peblo:peblodev@localhost:5434/peblo"
    )
    # Synchronous URL used only by Alembic migrations
    DATABASE_SYNC_URL: str = (
        "postgresql+psycopg://peblo:peblodev@localhost:5434/peblo"
    )

    # ── JWT Auth ─────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Seeded users (created by seed script) ────────────────────────
    ADMIN_EMAIL: str = "admin@peblo.local"
    ADMIN_PASSWORD: str = "admin123"
    EDITOR_EMAIL: str = "editor@peblo.local"
    EDITOR_PASSWORD: str = "editor123"

    # ── Storage ───────────────────────────────────────────────────────
    STORAGE_BACKEND: str = "local"  # local | minio | r2 | b2 | supabase
    LOCAL_STORAGE_PATH: str = "./storage"
    LOCAL_STORAGE_BASE_URL: str = "http://localhost:8000/static"

    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "peblo"

    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""

    B2_KEY_ID: str = ""
    B2_APPLICATION_KEY: str = ""
    B2_BUCKET_NAME: str = ""
    B2_ENDPOINT_URL: str = ""

    SUPABASE_PROJECT_ID: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_S3_ACCESS_KEY: str = ""
    SUPABASE_S3_SECRET_KEY: str = ""
    SUPABASE_BUCKET: str = "peblo"

    # ── Application ───────────────────────────────────────────────────
    APP_NAME: str = "Peblo TV API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:5174"]

    # ── Seed ──────────────────────────────────────────────────────────
    SEED_FILE_PATH: str = "../seed_shows.json"

    @property
    def storage_path(self) -> Path:
        return Path(self.LOCAL_STORAGE_PATH)


@lru_cache
def get_settings() -> Settings:
    return Settings()
