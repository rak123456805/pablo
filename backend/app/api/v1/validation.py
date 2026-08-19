"""Validation report endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_editor
from app.database import get_db
from app.models import User
from app.schemas import ValidationReport
from app.services.validator import build_validation_report

router = APIRouter(prefix="/admin/validation", tags=["validation"])


@router.get("/report", response_model=ValidationReport)
async def get_validation_report(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_editor),
):
    """
    Return all current issues blocking publication, grouped for editors.
    Read-only — does not modify any data.
    """
    return await build_validation_report(db)
