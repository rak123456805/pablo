import asyncio
import sys
import json
sys.path.insert(0, 'backend')

from app.database import get_session_factory
from app.models import Show, Episode
from app.services.artwork_storage import get_storage
from app.services.publisher import CATALOG_KEY
from sqlalchemy import select

async def main():
    factory = get_session_factory()
    async with factory() as db:
        res = await db.execute(select(Show))
        shows = list(res.scalars().all())
        print("=== SHOWS CURRENTLY IN POSTGRES DATABASE ===")
        for s in shows:
            print(f"- ID: {s.id} | Slug: {s.slug} | Title: '{s.title}' | Status: {s.status} | Section: {s.section}")

    print("\n=== SHOWS CURRENTLY IN SUPABASE CATALOG.JSON ===")
    storage = get_storage()
    if storage.exists(CATALOG_KEY):
        data = await storage.get(CATALOG_KEY)
        catalog = json.loads(data)
        for sec, s_list in catalog.get("sections", {}).items():
            print(f"Section: {sec}")
            for s in s_list:
                print(f"  - Title: '{s['title']}' | ID: {s.get('id')}")
    else:
        print("No catalog.json found.")

if __name__ == "__main__":
    asyncio.run(main())
