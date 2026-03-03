import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app


@pytest.fixture
async def db_session():
    """Create an isolated test database for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    os.unlink(db_path)


@pytest.fixture
async def client(db_session: AsyncSession):
    """HTTP client wired to use the test database."""

    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def upload_dir(tmp_path):
    """Provide a temp upload directory and patch settings."""
    from app.config import settings

    original = settings.upload_dir
    settings.upload_dir = str(tmp_path / "uploads")
    yield settings.upload_dir
    settings.upload_dir = original
