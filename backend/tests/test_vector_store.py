import pytest

from app.services.vector_store import VectorStore


@pytest.fixture
def store(chroma_dir):
    return VectorStore(persist_dir=chroma_dir)


def test_add_and_search(store: VectorStore):
    """Test basic insert and retrieval."""
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    store.add(
        ids=["c1", "c2", "c3"],
        embeddings=embeddings,
        documents=["chunk about cats", "chunk about dogs", "chunk about birds"],
        metadatas=[
            {"document_id": "doc1", "chunk_index": 0, "page_number": 1},
            {"document_id": "doc1", "chunk_index": 1, "page_number": 1},
            {"document_id": "doc2", "chunk_index": 0, "page_number": 1},
        ],
    )

    # Search with query close to first embedding
    results = store.search(
        query_embedding=[0.9, 0.1, 0.0],
        document_ids=["doc1", "doc2"],
        top_k=2,
    )
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[0].score > 0.5


def test_search_with_document_filter(store: VectorStore):
    """Search should respect document_id filtering."""
    store.add(
        ids=["c1", "c2"],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        documents=["doc1 content", "doc2 content"],
        metadatas=[
            {"document_id": "doc1", "chunk_index": 0, "page_number": 1},
            {"document_id": "doc2", "chunk_index": 0, "page_number": 1},
        ],
    )

    # Filter to doc2 only — should return doc2 even though query is closer to doc1
    results = store.search(
        query_embedding=[0.9, 0.1],
        document_ids=["doc2"],
        top_k=5,
    )
    assert len(results) == 1
    assert results[0].document_id == "doc2"


def test_delete_by_document(store: VectorStore):
    """Deleting by document_id should remove all its chunks."""
    store.add(
        ids=["c1", "c2", "c3"],
        embeddings=[[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]],
        documents=["a", "b", "c"],
        metadatas=[
            {"document_id": "doc1", "chunk_index": 0, "page_number": 1},
            {"document_id": "doc1", "chunk_index": 1, "page_number": 1},
            {"document_id": "doc2", "chunk_index": 0, "page_number": 1},
        ],
    )

    store.delete_by_document("doc1")

    # Only doc2 chunk should remain
    results = store.search(
        query_embedding=[0.5, 0.5],
        document_ids=["doc1", "doc2"],
        top_k=10,
    )
    assert len(results) == 1
    assert results[0].document_id == "doc2"


def test_search_returns_metadata(store: VectorStore):
    """Verify search results include all metadata fields."""
    store.add(
        ids=["c1"],
        embeddings=[[1.0, 0.0]],
        documents=["test content"],
        metadatas=[{"document_id": "doc1", "chunk_index": 3, "page_number": 5}],
    )

    results = store.search(
        query_embedding=[1.0, 0.0],
        document_ids=["doc1"],
        top_k=1,
    )
    assert len(results) == 1
    r = results[0]
    assert r.chunk_id == "c1"
    assert r.document_id == "doc1"
    assert r.chunk_index == 3
    assert r.page_number == 5
    assert r.content == "test content"
    assert r.score > 0
