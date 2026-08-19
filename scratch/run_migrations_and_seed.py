import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy import text
from app.database import get_engine, get_session_factory, Base
from app.services.seed_importer import import_seed_file
from app.models import User, Show, Episode, Season

async def main():
    engine = get_engine()
    print("1. Creating database tables if missing...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   Tables created successfully!")

    factory = get_session_factory()
    async with factory() as session:
        # 2. Create default admin and editor users
        print("2. Ensuring default system users (admin@peblo.local & editor@peblo.local)...")
        from sqlalchemy import select
        from app.core.security import hash_password
        res = await session.execute(select(User).where(User.email == "admin@peblo.local"))
        admin = res.scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin@peblo.local",
                hashed_password=hash_password("admin123"),
                role="admin",
                is_active=True
            )
            session.add(admin)
            print("   Created admin@peblo.local (role=admin)")

        res = await session.execute(select(User).where(User.email == "editor@peblo.local"))
        editor = res.scalar_one_or_none()
        if not editor:
            editor = User(
                email="editor@peblo.local",
                hashed_password=hash_password("editor123"),
                role="editor",
                is_active=True
            )
            session.add(editor)
            print("   Created editor@peblo.local (role=editor)")
        
        await session.commit()

        # 3. Seed challenge data from seed_shows.json
        print("3. Seeding challenge data from seed_shows.json...")
        res = await session.execute(select(Show))
        shows = res.scalars().all()
        if len(shows) == 0:
            seed_res = await import_seed_file(session, "seed_shows.json")
            seed_res.print_summary()
        else:
            print(f"   Database already seeded with {len(shows)} shows!")

        # 4. Check show statuses and validation summary
        shows_res = await session.execute(select(Show))
        all_shows = shows_res.scalars().all()
        published_shows = [s for s in all_shows if s.status == "published"]
        draft_shows = [s for s in all_shows if s.status == "draft"]
        
        print(f"\nTotal shows in DB    : {len(all_shows)}")
        print(f"  Published shows    : {len(published_shows)}")
        print(f"  Draft shows        : {len(draft_shows)}")

        episodes_res = await session.execute(select(Episode))
        all_episodes = episodes_res.scalars().all()
        published_episodes = [e for e in all_episodes if e.status == "published"]
        draft_episodes = [e for e in all_episodes if e.status == "draft"]
        
        print(f"Total episodes in DB : {len(all_episodes)}")
        print(f"  Published episodes : {len(published_episodes)}")
        print(f"  Draft episodes     : {len(draft_episodes)}")

if __name__ == "__main__":
    asyncio.run(main())
