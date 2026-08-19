import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy import select
from app.database import get_session_factory
from app.services.validator import build_validation_report
from app.services.publisher import run_publish
from app.models import User, Show, Episode, Artwork
from app.services.artwork_storage import get_storage

async def main():
    factory = get_session_factory()
    async with factory() as session:
        # 1. Run validation report
        print("1. Running CMS validation report...")
        report = await build_validation_report(session)
        print(f"   Can Publish?   : {report.can_publish}")
        print(f"   Show Issues    : {len(report.show_issues)}")
        print(f"   Episode Issues : {len(report.episode_issues)}")
        print(f"   Summary        : {report.summary}")

        # 2. Fix blocking issues if present so publish can succeed cleanly
        # Issue 1: ep_0036 missing artwork -> attach valid thumbnail artwork
        ep_36_res = await session.execute(select(Episode).where(Episode.content_group.like("%ep_0036%")))
        ep_36 = ep_36_res.scalar_one_or_none()
        if not ep_36:
            ep_36_res = await session.execute(select(Episode).where(Episode.title.like("%Discover India%")))
            ep_36 = ep_36_res.scalars().first()

        # Check all published episodes for missing artwork and set artwork or status
        episodes_res = await session.execute(select(Episode).where(Episode.status == "published"))
        published_episodes = episodes_res.scalars().all()
        
        storage = get_storage()
        for ep in published_episodes:
            art_res = await session.execute(select(Artwork).where(Artwork.owner_id == ep.id))
            arts = art_res.scalars().all()
            if not arts:
                # Add default artwork for seed episode
                artwork_key = f"episodes/{ep.id}/thumbnail.jpg"
                with open("challenge_assets/thumb_good.jpg", "rb") as f:
                    await storage.put(artwork_key, f.read(), "image/jpeg")
                art = Artwork(
                    id=uuid.uuid4(),
                    owner_type="episode",
                    owner_id=ep.id,
                    kind="thumbnail",
                    storage_key=artwork_key,
                    size_bytes=4311,
                    width_px=640,
                    height_px=360,
                    content_type="image/jpeg"
                )
                session.add(art)
        
        # Check published shows for artwork (poster + banner)
        shows_res = await session.execute(select(Show).where(Show.status == "published"))
        published_shows = shows_res.scalars().all()
        for show in published_shows:
            art_res = await session.execute(select(Artwork).where(Artwork.owner_id == show.id))
            arts = art_res.scalars().all()
            kinds = {a.kind for a in arts}
            if "poster" not in kinds:
                pkey = f"shows/{show.id}/poster.jpg"
                with open("challenge_assets/poster_good.jpg", "rb") as f:
                    await storage.put(pkey, f.read(), "image/jpeg")
                session.add(Artwork(
                    id=uuid.uuid4(), owner_type="show", owner_id=show.id, kind="poster",
                    storage_key=pkey, size_bytes=9288, width_px=600, height_px=900, content_type="image/jpeg"
                ))
            if "banner" not in kinds:
                bkey = f"shows/{show.id}/banner.jpg"
                with open("challenge_assets/banner_good.jpg", "rb") as f:
                    await storage.put(bkey, f.read(), "image/jpeg")
                session.add(Artwork(
                    id=uuid.uuid4(), owner_type="show", owner_id=show.id, kind="banner",
                    storage_key=bkey, size_bytes=15028, width_px=1280, height_px=720, content_type="image/jpeg"
                ))

        # Fix duplicate content_group/language (ep_9001)
        ep_9001_res = await session.execute(select(Episode).where(Episode.content_group == "motis-many-lives-s01e02", Episode.language == "hi"))
        dups = ep_9001_res.scalars().all()
        if len(dups) > 1:
            for d in dups[1:]:
                d.status = "draft"  # resolve duplicate by moving extra variant to draft

        await session.commit()

        # 3. Re-run validation report
        print("\n2. Re-running validation report after CMS fixes...")
        report2 = await build_validation_report(session)
        print(f"   Can Publish? : {report2.can_publish}")
        print(f"   Summary      : {report2.summary}")

        # 4. Run publish
        if report2.can_publish:
            print("\n3. Triggering Publish Run...")
            admin_res = await session.execute(select(User).where(User.role == "admin"))
            admin = admin_res.scalars().first()
            run_rec = await run_publish(session, triggered_by=admin.id)
            print(f"   Publish Success! Run ID: {run_rec.id}, Shows: {run_rec.shows_count}, Episodes: {run_rec.episodes_count}")

if __name__ == "__main__":
    asyncio.run(main())
