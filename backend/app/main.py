"""FastAPI application factory."""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.v1.router import router
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import TokenRequest


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_origin_regex=r"https://.*\.vercel\.app|http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount local storage for artwork serving
    storage_path = settings.storage_path
    storage_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(storage_path)), name="static")

    import os
    test_assets_path = Path("challenge_assets")
    if test_assets_path.exists():
        app.mount("/test_assets", StaticFiles(directory=str(test_assets_path)), name="test_assets")

    app.include_router(router)

    # Route aliases at root level for Vercel deployment compatibility
    @app.get("/catalog", tags=["catalog"])
    async def get_catalog_root(db: AsyncSession = Depends(get_db)):
        from app.api.v1.catalog import get_catalog
        return await get_catalog(db)

    @app.post("/auth/token", tags=["auth"])
    @app.post("/auth/login", tags=["auth"])
    async def login_root(body: TokenRequest, db: AsyncSession = Depends(get_db)):
        from app.api.v1.auth import login
        return await login(body, db)

    @app.get("/auth/me", tags=["auth"])
    async def me_root(current_user: User = Depends(get_current_user)):
        from app.api.v1.auth import me
        return await me(current_user)

    @app.get("/health", tags=["health"])
    async def health(db: AsyncSession = Depends(get_db)):
        """Health check — verifies API is reachable."""
        from sqlalchemy import text
        db_status = "ok"
        try:
            await db.execute(text("SELECT 1"))
        except Exception as exc:
            db_status = f"error: {exc}"

        storage_status = "ok"
        try:
            from app.services.artwork_storage import get_storage
            get_storage()
        except Exception as exc:
            storage_status = f"error: {exc}"

        return {
            "status": "ok" if db_status == "ok" and storage_status == "ok" else "degraded",
            "version": settings.APP_VERSION,
            "db": db_status,
            "storage": storage_status,
        }

    return app


app = create_app()
