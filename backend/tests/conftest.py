import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.conversation import Conversation, Message


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
    """HTTP client wired to use the test database, with pipeline mocked."""

    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    # Mock process_document so upload tests don't need real embeddings/vector store
    mock_pipeline = AsyncMock()

    async def fake_pipeline(doc_id, file_path, file_type, db):
        from sqlalchemy import select

        from app.models.document import Document

        result = await db.execute(select(Document).where(Document.id == doc_id))
        document = result.scalar_one_or_none()
        if document:
            document.status = "ready"
            document.page_count = 1
            await db.flush()

    mock_pipeline.side_effect = fake_pipeline

    with patch("app.routers.documents.process_document", mock_pipeline):
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
async def conversation_with_messages(db_session):
    """Create a conversation with messages for testing."""
    conv = Conversation(title="Test conversation")
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


@pytest.fixture
def chroma_dir(tmp_path):
    """Provide a temp ChromaDB directory and patch settings."""
    from app.config import settings

    original = settings.chroma_persist_dir
    settings.chroma_persist_dir = str(tmp_path / "chroma")
    yield settings.chroma_persist_dir
    settings.chroma_persist_dir = original
