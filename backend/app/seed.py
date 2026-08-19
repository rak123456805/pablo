"""
CLI entry point to migrate database and seed challenge data from seed_shows.json.
Usage:
    python -m app.seed
"""
from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.database import Base, get_engine, get_session_factory
from app.models import Episode, Show, User
from app.services.seed_importer import import_seed_file


async def run_seed():
    engine = get_engine()
    print("1. Running database migrations / creating schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   Database schema ready!")

    factory = get_session_factory()
    async with factory() as session:
        # Create system users
        print("2. Ensuring default system accounts (admin@peblo.local, editor@peblo.local)...")
        res = await session.execute(select(User).where(User.email == "admin@peblo.local"))
        if not res.scalar_one_or_none():
            admin = User(
                email="admin@peblo.local",
                hashed_password=hash_password("admin123"),
                role="admin",
                is_active=True,
            )
            session.add(admin)
            print("   Created admin@peblo.local (role=admin)")

        res = await session.execute(select(User).where(User.email == "editor@peblo.local"))
        if not res.scalar_one_or_none():
            editor = User(
                email="editor@peblo.local",
                hashed_password=hash_password("editor123"),
                role="editor",
                is_active=True,
            )
            session.add(editor)
            print("   Created editor@peblo.local (role=editor)")

        await session.commit()

        # Seed challenge dataset
        print("3. Checking seed dataset...")
        shows_res = await session.execute(select(Show))
        shows = shows_res.scalars().all()
        if len(shows) == 0:
            print("   Seeding seed_shows.json into PostgreSQL...")
            seed_path = os.getenv("SEED_FILE_PATH", "seed_shows.json")
            if not os.path.exists(seed_path):
                seed_path = "../seed_shows.json"
            result = await import_seed_file(session, seed_path)
            result.print_summary()
        else:
            print(f"   Database already seeded with {len(shows)} shows!")

        # Status summary
        shows_res = await session.execute(select(Show))
        all_shows = shows_res.scalars().all()
        episodes_res = await session.execute(select(Episode))
        all_episodes = episodes_res.scalars().all()

        print(f"\nDB State Summary:")
        print(f"  Total Shows    : {len(all_shows)} (Published: {len([s for s in all_shows if s.status == 'published'])}, Draft: {len([s for s in all_shows if s.status == 'draft'])})")
        print(f"  Total Episodes : {len(all_episodes)} (Published: {len([e for e in all_episodes if e.status == 'published'])}, Draft: {len([e for e in all_episodes if e.status == 'draft'])})")


if __name__ == "__main__":
    asyncio.run(run_seed())
