import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.conversation import Conversation, Message

TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_NAME = "Test User"


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
    """HTTP client wired to use the test database, auto-registered and authenticated."""

    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    # Mock _run_pipeline_background so upload tests don't need real embeddings/vector store
    # The background task uses its own db session, so we mock the entire background function
    mock_bg_pipeline = AsyncMock()

    with patch("app.routers.documents._run_pipeline_background", mock_bg_pipeline):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            # Auto-register a test user so all endpoints work
            resp = await ac.post(
                "/api/auth/register",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD,
                    "name": TEST_USER_NAME,
                },
            )
            assert resp.status_code == 201
            # Store cookies from registration for subsequent requests
            ac.cookies.update(resp.cookies)
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def unauth_client(db_session: AsyncSession):
    """HTTP client with no auth cookies, for testing 401s."""

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


@pytest.fixture
async def conversation_with_messages(db_session, client):
    """Create a conversation with messages for testing."""
    # Get the test user's ID from the client
    resp = await client.get("/api/auth/me")
    user_id = resp.json()["id"]

    conv = Conversation(title="Test conversation", user_id=user_id)
    db_session.add(conv)
    await db_session.flush()

    msg1 = Message(conversation_id=conv.id, role="user", content="Hello")
    msg2 = Message(
        conversation_id=conv.id,
        role="assistant",
        content="Hi there!",
        source_chunks='[{"chunk_id": "c1", "filename": "test.pdf"}]',
    )
    db_session.add_all([msg1, msg2])
    await db_session.flush()
    return conv


