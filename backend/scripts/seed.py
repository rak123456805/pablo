"""
Seed script — imports seed_shows.json into the DB and creates the two system users.
Run with: python scripts/seed.py

This script:
1. Connects to Postgres
2. Creates admin and editor users
3. Imports all 95 seed rows (intentional bad data is preserved)
4. Prints an anomaly report
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import hash_password
from app.database import get_session_factory
from app.models import User
from app.services.seed_importer import import_seed_file


async def create_users(session: AsyncSession) -> None:
    settings = get_settings()
    users_to_create = [
        (settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD, "admin"),
        (settings.EDITOR_EMAIL, settings.EDITOR_PASSWORD, "editor"),
    ]
    for email, password, role in users_to_create:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                role=role,
            )
            session.add(user)
            print(f"  Created user: {email} ({role})")
        else:
            user.hashed_password = hash_password(password)
            user.role = role
            print(f"  Updated user: {email} ({role})")


async def main() -> None:
    settings = get_settings()
    seed_path = Path(settings.SEED_FILE_PATH)
    if not seed_path.exists():
        # Try relative to repo root
        seed_path = Path(__file__).parent.parent.parent / "seed_shows.json"
    if not seed_path.exists():
        print(f"ERROR: seed_shows.json not found. Tried {settings.SEED_FILE_PATH} and {seed_path}")
        sys.exit(1)

    print(f"Using seed file: {seed_path.resolve()}")
    factory = get_session_factory()

    async with factory() as session:
        print("\n-- Creating system users --")
        await create_users(session)

        print("\n-- Importing seed data --")
        result = await import_seed_file(session, seed_path)

        await session.commit()

    result.print_summary()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
