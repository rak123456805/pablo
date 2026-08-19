import asyncio
import os
import sys
import uuid
import json

sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy import select
from app.database import get_session_factory
from app.models import User, Show, Episode, Artwork
from app.services.publisher import run_publish, CATALOG_KEY
from app.services.artwork_storage import get_storage
from app.services.validator import build_validation_report

async def main():
    factory = get_session_factory()
    async with factory() as session:
        storage = get_storage()

        report = await build_validation_report(session)
        print("BLOCKING ISSUES BEFORE FIX:")
        for s in report.show_issues:
            for issue in s.issues:
                if issue.severity == "blocking":
                    print(f"  Show '{s.show_title}' -> [{issue.code}] {issue.message}")
        for e in report.episode_issues:
            for issue in e.issues:
                if issue.severity == "blocking":
                    print(f"  Episode '{e.episode_title}' ({e.episode_id}) -> [{issue.code}] {issue.message}")

        # Fix 1: Add artwork to ep_0036
        ep_36_res = await session.execute(select(Episode).where(Episode.external_id == "ep_0036"))
        ep_36 = ep_36_res.scalar_one_or_none()
        if ep_36:
            art_res = await session.execute(select(Artwork).where(Artwork.owner_id == ep_36.id))
            if not art_res.scalars().all():
                art_key = f"episodes/{ep_36.id}/thumbnail.jpg"
                with open("challenge_assets/thumb_good.jpg", "rb") as f:
                    await storage.put(art_key, f.read(), "image/jpeg")
                session.add(Artwork(
                    id=uuid.uuid4(), owner_type="episode", owner_id=ep_36.id, kind="thumbnail",
                    storage_key=art_key, size_bytes=4311, width_px=640, height_px=360, content_type="image/jpeg"
                ))

        # Fix 2: Reassign ep_9001 content_group to resolve duplicate
        ep_9001_res = await session.execute(select(Episode).where(Episode.external_id == "ep_9001"))
        ep_9001 = ep_9001_res.scalar_one_or_none()
        if ep_9001:
            ep_9001.content_group = "motis-many-lives-s01e02-v2"
            ep_9001.status = "draft"

        # Fix 3: Add artwork for all published episodes/shows
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

        episodes_res = await session.execute(select(Episode).where(Episode.status == "published"))
        published_episodes = episodes_res.scalars().all()
        for ep in published_episodes:
            art_res = await session.execute(select(Artwork).where(Artwork.owner_id == ep.id))
            arts = art_res.scalars().all()
            if not arts:
                artwork_key = f"episodes/{ep.id}/thumbnail.jpg"
                with open("challenge_assets/thumb_good.jpg", "rb") as f:
                    await storage.put(artwork_key, f.read(), "image/jpeg")
                session.add(Artwork(
                    id=uuid.uuid4(), owner_type="episode", owner_id=ep.id, kind="thumbnail",
                    storage_key=artwork_key, size_bytes=4311, width_px=640, height_px=360, content_type="image/jpeg"
                ))

        await session.commit()

        # Check validation again
        report2 = await build_validation_report(session)
        print(f"\nVALIDATION REPORT AFTER FIX: Can Publish = {report2.can_publish}, Summary = {report2.summary}")
        if not report2.can_publish:
            for s in report2.show_issues:
                for issue in s.issues:
                    if issue.severity == "blocking":
                        print(f"  Show '{s.show_title}' -> [{issue.code}] {issue.message}")
            for e in report2.episode_issues:
                for issue in e.issues:
                    if issue.severity == "blocking":
                        print(f"  Episode '{e.episode_title}' ({e.episode_id}) -> [{issue.code}] {issue.message}")

        if report2.can_publish:
            admin_res = await session.execute(select(User).where(User.role == "admin"))
            admin = admin_res.scalars().first()
            print("\nTRIGGERING PUBLISH RUN...")
            run_rec = await run_publish(session, triggered_by=admin.id)
            print(f"   Publish Success! Run ID: {run_rec.id}")
            print(f"   Published Shows   : {run_rec.shows_count}")
            print(f"   Published Episodes: {run_rec.episodes_count}")
            print(f"   Catalog Storage Key: {run_rec.catalog_key}")
            print(f"   Storage Public URL : {storage.public_url(CATALOG_KEY)}")

            print("\nVERIFYING GET /catalog JSON:")
            cat_bytes = await storage.get(CATALOG_KEY)
            cat_json = json.loads(cat_bytes)
            for sec, s_list in cat_json.get("sections", {}).items():
                if s_list:
                    print(f"  Section '{sec}': {len(s_list)} show(s) -> {[s['title'] for s in s_list]}")

if __name__ == "__main__":
    asyncio.run(main())
