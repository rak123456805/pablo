"""API v1 router — aggregates all sub-routers for both /api/v1/ and root / paths."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import artwork, auth, catalog, episodes, seasons, shows, validation

# Unprefixed router (supports direct root endpoints like /admin/shows, /auth/token, /catalog)
unprefixed_router = APIRouter()
unprefixed_router.include_router(auth.router)
unprefixed_router.include_router(shows.router, prefix="/admin")
unprefixed_router.include_router(seasons.router, prefix="/admin")
unprefixed_router.include_router(episodes.router, prefix="/admin")
unprefixed_router.include_router(artwork.router, prefix="/admin")
unprefixed_router.include_router(validation.router)
unprefixed_router.include_router(catalog.router)
unprefixed_router.include_router(catalog.admin_router)

# /api/v1 prefixed router
router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(shows.router, prefix="/admin")
router.include_router(seasons.router, prefix="/admin")
router.include_router(episodes.router, prefix="/admin")
router.include_router(artwork.router, prefix="/admin")
router.include_router(validation.router)
router.include_router(catalog.router)
router.include_router(catalog.admin_router)
