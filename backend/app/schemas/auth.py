"""
Pydantic schemas for authentication endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class TokenRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("editor", "admin"):
            raise ValueError(f"Invalid role: {v}")
        return v
