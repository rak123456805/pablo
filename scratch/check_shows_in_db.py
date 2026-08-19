import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy import select
from app.database import get_session_factory
from app.models import Show, Episode, Season

async def main():
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(select(Show))
        shows = res.scalars().all()
        print(f"Total shows in DB: {len(shows)}")
        for s in shows:
            print(f"  Show: id={s.id} | title='{s.title}' | status='{s.status}' | section='{s.section}' | categories={s.categories}")
            eps_res = await session.execute(select(Episode).where(Episode.show_id == s.id))
            eps = eps_res.scalars().all()
            print(f"    Episodes count: {len(eps)} (published: {len([e for e in eps if e.status == 'published'])})")

if __name__ == "__main__":
    asyncio.run(main())
