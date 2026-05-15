"""Integration test for pgvector search.

Skipped on SQLite (default test dialect) because cosine_distance is a
Postgres-only operator. To run, set DATABASE_URL to a Postgres instance
with the pgvector extension installed.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.user import User
from app.services.auth import hash_password
from app.services.vector_store import search_chunks


@pytest.fixture
async def pg_session(db_session: AsyncSession):
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("pgvector search requires Postgres")
    # Ensure extension is available on the test DB
    await db_session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    return db_session


@pytest.fixture
async def owner(pg_session: AsyncSession) -> User:
    """Document.user_id is NOT NULL — every test doc needs an owner."""
    u = User(email=f"owner-{uuid.uuid4()}@test", hashed_password=hash_password("x"), name="O")
    pg_session.add(u)
    await pg_session.flush()
    return u


async def test_search_orders_by_similarity_and_filters(pg_session: AsyncSession, owner: User):
    doc_a = Document(
        id=str(uuid.uuid4()), user_id=owner.id, filename="a.pdf",
        file_type="pdf", size_bytes=1, status="ready",
    )
    doc_b = Document(
        id=str(uuid.uuid4()), user_id=owner.id, filename="b.pdf",
        file_type="pdf", size_bytes=1, status="ready",
    )
    pg_session.add_all([doc_a, doc_b])
    await pg_session.flush()

    # Pad embeddings to the configured dim
    from app.config import settings

    def pad(v: list[float]) -> list[float]:
        return v + [0.0] * (settings.embedding_dimensions - len(v))

    chunks = [
        Chunk(
            document_id=doc_a.id, chunk_index=0, page_number=1,
            content="cats", token_count=1, embedding=pad([1.0, 0.0, 0.0]),
        ),
        Chunk(
            document_id=doc_a.id, chunk_index=1, page_number=1,
            content="dogs", token_count=1, embedding=pad([0.0, 1.0, 0.0]),
        ),
        Chunk(
            document_id=doc_b.id, chunk_index=0, page_number=1,
            content="birds", token_count=1, embedding=pad([0.0, 0.0, 1.0]),
        ),
    ]
    pg_session.add_all(chunks)
    await pg_session.flush()

    # Query close to first chunk; restrict to doc_a only
    results = await search_chunks(
        db=pg_session,
        query_embedding=pad([0.9, 0.1, 0.0]),
        document_ids=[doc_a.id],
        top_k=5,
    )
    assert [r.content for r in results] == ["cats", "dogs"]
    assert all(r.document_id == doc_a.id for r in results)
    assert results[0].score > results[1].score


async def test_search_skips_chunks_without_embeddings(pg_session: AsyncSession, owner: User):
    doc = Document(
        id=str(uuid.uuid4()), user_id=owner.id, filename="x.pdf",
        file_type="pdf", size_bytes=1, status="ready",
    )
    pg_session.add(doc)
    await pg_session.flush()

    from app.config import settings

    pg_session.add(
        Chunk(
            document_id=doc.id, chunk_index=0, page_number=1,
            content="no-vec", token_count=1, embedding=None,
        ),
    )
    await pg_session.flush()

    results = await search_chunks(
        db=pg_session,
        query_embedding=[0.1] * settings.embedding_dimensions,
        document_ids=[doc.id],
        top_k=5,
    )
    assert results == []
