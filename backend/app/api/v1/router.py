"""API v1 router — aggregates all sub-routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import artwork, auth, catalog, episodes, seasons, shows, validation

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(shows.router, prefix="/admin")
router.include_router(seasons.router, prefix="/admin")
router.include_router(episodes.router, prefix="/admin")
router.include_router(artwork.router, prefix="/admin")
router.include_router(validation.router)
router.include_router(catalog.router)
router.include_router(catalog.admin_router)
