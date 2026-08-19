"""
Test fixtures and shared setup.

Uses PostgreSQL test database (peblo_test on port 5433).
The DB_TEST_URL env var overrides the default connection.
"""
import os
import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_URL = os.getenv(
    "DB_TEST_URL",
    "postgresql+asyncpg://peblo:peblodev@localhost:5433/peblo_test",
)
TEST_SYNC_URL = TEST_DB_URL.replace("+asyncpg", "+psycopg")
TEST_STORAGE_PATH = Path(__file__).parent / "fixtures" / "storage"

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["DATABASE_SYNC_URL"] = TEST_SYNC_URL
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_PATH"] = str(TEST_STORAGE_PATH)
os.environ["LOCAL_STORAGE_BASE_URL"] = "http://testserver/static"

from app.database import Base  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_storage():
    """
    Reset the storage singleton and clear the test storage directory before each test.

    Without this, a test that writes catalog.json would pollute a subsequent test
    that expects no catalogue to exist yet.
    """
    import app.services.artwork_storage as _storage_mod
    _storage_mod._storage_instance = None  # reset singleton

    # Clean the test storage directory
    if TEST_STORAGE_PATH.exists():
        shutil.rmtree(TEST_STORAGE_PATH)
    TEST_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

    yield  # run the test

    # Post-test cleanup (belt-and-suspenders)
    _storage_mod._storage_instance = None



@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False, pool_pre_ping=True)
    async with eng.begin() as conn:
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(engine) -> AsyncSession:
    """Yield an AsyncSession for the test."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession):
    """HTTP client with DB session overridden to use test session."""
    from app.database import get_db

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession):
    from app.core.security import hash_password
    from app.models import User

    user = User(
        email="test_admin@peblo.tv",
        hashed_password=hash_password("adminpass"),
        role="admin",
    )
    db.add(user)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def editor_user(db: AsyncSession):
    from app.core.security import hash_password
    from app.models import User

    user = User(
        email="test_editor@peblo.tv",
        hashed_password=hash_password("editorpass"),
        role="editor",
    )
    db.add(user)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email": admin_user.email, "password": "adminpass"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def editor_token(client, editor_user):
    resp = await client.post(
        "/api/v1/auth/token",
        json={"email": editor_user.email, "password": "editorpass"},
    )
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
