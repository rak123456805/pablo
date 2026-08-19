import asyncio
from app.services.artwork_storage import get_storage
from app.services.publisher import CATALOG_KEY
import json

async def main():
    storage = get_storage()
    if storage.exists(CATALOG_KEY):
        data = await storage.get(CATALOG_KEY)
        catalog = json.loads(data)
        print("Catalog generated_at:", catalog.get("generated_at"))
        shows = []
        for sec, s_list in catalog.get("sections", {}).items():
            for s in s_list:
                shows.append(s["title"])
        print("Shows in published catalog.json:", shows)
    else:
        print("No catalog.json found in storage.")

if __name__ == "__main__":
    asyncio.run(main())
