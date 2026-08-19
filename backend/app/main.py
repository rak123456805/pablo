"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router
from app.config import get_settings


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
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount local storage for artwork serving
    storage_path = settings.storage_path
    storage_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(storage_path)), name="static")

    app.include_router(router)

    @app.get("/health", tags=["health"])
    async def health():
        """Health check — verifies API is reachable."""
        from sqlalchemy import text
        from app.database import get_session_factory
        db_status = "ok"
        try:
            factory = get_session_factory()
            async with factory() as session:
                await session.execute(text("SELECT 1"))
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
