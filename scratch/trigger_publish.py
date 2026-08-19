import asyncio
import sys
sys.path.insert(0, 'backend')

from app.database import get_session_factory
from app.models import User
from app.services.publisher import run_publish
from sqlalchemy import select

async def main():
    factory = get_session_factory()
    async with factory() as db:
        res = await db.execute(select(User).where(User.role == "admin"))
        admin = res.scalars().first()
        if not admin:
            print("No admin user found.")
            return

        print(f"Triggering publish as admin: {admin.email} (ID: {admin.id})...")
        try:
            run = await run_publish(db, triggered_by=admin.id)
            print(f"Publish successful! Run ID: {run.id} | Status: {run.status}")
            print(f"Published shows count: {run.shows_count} | Episodes count: {run.episodes_count}")
        except Exception as exc:
            print(f"Publish failed: {exc}")

if __name__ == "__main__":
    asyncio.run(main())
