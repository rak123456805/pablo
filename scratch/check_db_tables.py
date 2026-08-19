import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy import text
from app.database import get_db, get_engine
from app.config import get_settings

async def check():
    settings = get_settings()
    print("Database URL:", settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL)
    async with get_engine().connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = [r[0] for r in result.fetchall()]
        print("Existing tables:", tables)
        
        for table in ["users", "shows", "seasons", "episodes", "artworks", "publish_runs"]:
            if table in tables:
                count_res = await conn.execute(text(f"SELECT count(*) FROM {table};"))
                print(f"  Count {table}: {count_res.scalar()}")
            else:
                print(f"  Table '{table}' MISSING!")

if __name__ == "__main__":
    asyncio.run(check())
