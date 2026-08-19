import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath("backend"))

from app.config import get_settings
from app.services.artwork_storage import SupabaseStorage

async def test():
    settings = get_settings()
    storage = SupabaseStorage(
        project_id=settings.SUPABASE_PROJECT_ID or "yxlpuwplaonbagxuwdnq",
        service_role_key=settings.SUPABASE_SERVICE_ROLE_KEY or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl4bHB1d3BsYW9uYmFneHV3ZG5xIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzE1MDgwMywiZXhwIjoyMTAyNzI2ODAzfQ.W3plXloo24p7Osf_TkIuUdwmGlA3xIdSJ0CRBvQ9grg",
        bucket="peblo"
    )

    with open("challenge_assets/banner_good.jpg", "rb") as f:
        data = f.read()

    key = "shows/test_show_123/banner.jpg"
    print("Uploading to Supabase Storage via SupabaseStorage class...")
    public_url = await storage.put(key, data, "image/jpeg")
    print("Upload succeeded! Public URL:", public_url)

    print("Checking exists():", storage.exists(key))
    fetched_data = await storage.get(key)
    print("Fetched bytes length:", len(fetched_data))

if __name__ == "__main__":
    asyncio.run(test())
