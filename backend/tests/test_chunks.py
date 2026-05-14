import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document


@pytest.fixture
async def document_with_chunks(db_session: AsyncSession, client):
    """Create a document with 5 chunks across 2 pages."""
    # Get the test user's ID
    me_resp = await client.get("/api/auth/me")
    user_id = me_resp.json()["id"]

    doc = Document(
        id="doc-1",
        user_id=user_id,
        filename="test.pdf",
        file_type="pdf",
        size_bytes=1024,
        status="ready",
        page_count=2,
    )
    db_session.add(doc)
    await db_session.flush()

    chunks = []
    for i in range(5):
        chunk = Chunk(
            id=f"chunk-{i}",
            document_id="doc-1",
            chunk_index=i,
            page_number=1 if i < 3 else 2,
            content=f"Content of chunk {i}",
            token_count=10 + i,
        )
        chunks.append(chunk)
    db_session.add_all(chunks)
    await db_session.flush()
    return doc, chunks


@pytest.mark.asyncio
async def test_list_chunks(client, document_with_chunks):
    resp = await client.get("/api/documents/doc-1/chunks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"] == "doc-1"
    assert data["total"] == 5
    assert len(data["chunks"]) == 5
    # Verify ordered by chunk_index
    indices = [c["chunk_index"] for c in data["chunks"]]
    assert indices == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_list_chunks_filter_by_page(client, document_with_chunks):
    resp = await client.get("/api/documents/doc-1/chunks?page=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert all(c["page_number"] == 1 for c in data["chunks"])

    resp2 = await client.get("/api/documents/doc-1/chunks?page=2")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total"] == 2
    assert all(c["page_number"] == 2 for c in data2["chunks"])


@pytest.mark.asyncio
async def test_list_chunks_document_not_found(client):
    resp = await client.get("/api/documents/nonexistent/chunks")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_chunk_with_context_middle(client, document_with_chunks):
    """Middle chunk should have both previous and next."""
    resp = await client.get("/api/chunks/chunk-2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunk"]["id"] == "chunk-2"
    assert data["chunk"]["content"] == "Content of chunk 2"
    assert data["previous_chunk"]["id"] == "chunk-1"
    assert data["next_chunk"]["id"] == "chunk-3"
    assert data["document_filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_get_chunk_with_context_first(client, document_with_chunks):
    """First chunk should have no previous."""
    resp = await client.get("/api/chunks/chunk-0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunk"]["id"] == "chunk-0"
    assert data["previous_chunk"] is None
    assert data["next_chunk"]["id"] == "chunk-1"


@pytest.mark.asyncio
async def test_get_chunk_with_context_last(client, document_with_chunks):
    """Last chunk should have no next."""
    resp = await client.get("/api/chunks/chunk-4")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunk"]["id"] == "chunk-4"
    assert data["previous_chunk"]["id"] == "chunk-3"
    assert data["next_chunk"] is None


@pytest.mark.asyncio
async def test_get_chunk_not_found(client):
    resp = await client.get("/api/chunks/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_chunks_empty_page(client, document_with_chunks):
    """Filtering by a page with no chunks returns empty list."""
    resp = await client.get("/api/documents/doc-1/chunks?page=99")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["chunks"] == []
