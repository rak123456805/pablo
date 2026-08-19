import asyncio
import os
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.services.seed_importer import import_seed_file
from app.services.publisher import run_publish
from app.models import Show, Episode, Artwork
from app.services.artwork_storage import get_storage
from sqlalchemy import select

DB_URL = "sqlite+aiosqlite:///./test_dev.db"

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as db:
        print("Importing seed data from seed_shows.json...")
        res = await import_seed_file(db, "seed_shows.json")
        res.print_summary()
        
        # Attach valid sample test assets to first show and episode
        show_res = await db.execute(select(Show).where(Show.status == "published"))
        first_show = show_res.scalars().first()
        
        if first_show:
            print(f"Attaching sample artwork to show: {first_show.title} ({first_show.id})")
            storage = get_storage()
            
            # Read banner_good.jpg
            with open("challenge_assets/banner_good.jpg", "rb") as f:
                banner_bytes = f.read()
            banner_key = f"shows/{first_show.id}/banner.jpg"
            await storage.put(banner_key, banner_bytes, "image/jpeg")
            
            art_banner = Artwork(
                owner_type="show", owner_id=first_show.id, kind="banner",
                storage_key=banner_key, size_bytes=len(banner_bytes),
                width_px=1280, height_px=720, content_type="image/jpeg"
            )
            db.add(art_banner)
            
            # Read poster_good.jpg
            with open("challenge_assets/poster_good.jpg", "rb") as f:
                poster_bytes = f.read()
            poster_key = f"shows/{first_show.id}/poster.jpg"
            await storage.put(poster_key, poster_bytes, "image/jpeg")
            
            art_poster = Artwork(
                owner_type="show", owner_id=first_show.id, kind="poster",
                storage_key=poster_key, size_bytes=len(poster_bytes),
                width_px=600, height_px=900, content_type="image/jpeg"
            )
            db.add(art_poster)
            
            # Read thumb_good.jpg for first episode
            ep_res = await db.execute(select(Episode).where(Episode.show_id == first_show.id, Episode.status == "published"))
            first_ep = ep_res.scalars().first()
            if first_ep:
                with open("challenge_assets/thumb_good.jpg", "rb") as f:
                    thumb_bytes = f.read()
                thumb_key = f"episodes/{first_ep.id}/thumbnail.jpg"
                await storage.put(thumb_key, thumb_bytes, "image/jpeg")
                
                art_thumb = Artwork(
                    owner_type="episode", owner_id=first_ep.id, kind="thumbnail",
                    storage_key=thumb_key, size_bytes=len(thumb_bytes),
                    width_px=640, height_px=360, content_type="image/jpeg"
                )
                db.add(art_thumb)
                
            await db.commit()
        
        print("\nPublishing catalog...")
        admin_id = uuid.uuid4()
        pub_result = await run_publish(db, triggered_by=admin_id)
        print(f"Publish completed! Status: {pub_result.status}, Shows: {pub_result.shows_count}, Episodes: {pub_result.episodes_count}")

if __name__ == "__main__":
    asyncio.run(main())
