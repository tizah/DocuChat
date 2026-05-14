"""Tests for chat endpoint and RAG pipeline."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.document import Document
from app.services.rag import SourceChunk, build_context
from app.services.vector_store import SearchResult


@pytest.fixture
async def ready_document(db_session, client):
    """Create a ready document for chat testing."""
    me_resp = await client.get("/api/auth/me")
    user_id = me_resp.json()["id"]

    doc = Document(
        user_id=user_id,
        filename="test.pdf",
        file_type="application/pdf",
        size_bytes=1024,
        status="ready",
        page_count=3,
    )
    db_session.add(doc)
    await db_session.flush()
    return doc


# --- Unit tests for build_context ---


def test_build_context_basic():
    results = [
        SearchResult(
            chunk_id="c1",
            document_id="d1",
            chunk_index=0,
            content="Page one content.",
            page_number=1,
            score=0.9,
        ),
        SearchResult(
            chunk_id="c2",
            document_id="d2",
            chunk_index=0,
            content="Page two content.",
            page_number=2,
            score=0.8,
        ),
    ]
    filename_map = {"d1": "doc1.pdf", "d2": "doc2.pdf"}

    context, source_chunks = build_context(results, filename_map)

    assert "[Document: doc1.pdf, Page 1]" in context
    assert "Page one content." in context
    assert "[Document: doc2.pdf, Page 2]" in context
    assert len(source_chunks) == 2
    assert isinstance(source_chunks[0], SourceChunk)
    assert source_chunks[0].filename == "doc1.pdf"
    assert source_chunks[1].score == 0.8


def test_build_context_unknown_document():
    results = [
        SearchResult(
            chunk_id="c1",
            document_id="unknown",
            chunk_index=0,
            content="Some text.",
            page_number=1,
            score=0.5,
        ),
    ]
    context, source_chunks = build_context(results, {})
    assert "[Document: Unknown, Page 1]" in context
    assert source_chunks[0].filename == "Unknown"


def test_build_context_empty():
    context, source_chunks = build_context([], {})
    assert context == ""
    assert source_chunks == []


# --- Integration tests for chat endpoint ---


async def test_chat_no_documents(client: AsyncClient):
    resp = await client.post(
        "/api/chat",
        json={"message": "Hello", "document_ids": []},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "NO_DOCUMENTS"


async def test_chat_creates_conversation(client: AsyncClient, ready_document):
    mock_results = [
        SearchResult(
            chunk_id="c1",
            document_id=ready_document.id,
            chunk_index=0,
            content="Test chunk content.",
            page_number=1,
            score=0.95,
        ),
    ]

    def mock_stream(*args, **kwargs):
        yield "Hello "
        yield "world!"

    with (
        patch(
            "app.routers.chat.retrieve_chunks",
            new_callable=AsyncMock,
            return_value=mock_results,
        ),
        patch("app.routers.chat.stream_rag_response", side_effect=mock_stream),
    ):
        resp = await client.post(
            "/api/chat",
            json={
                "message": "What is this about?",
                "document_ids": [ready_document.id],
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")

        # Parse SSE events from response
        events = parse_sse_events(resp.text)
        event_types = [e["event"] for e in events if "event" in e]

        # SSE should contain at least a done event (metadata/token may vary)
        assert len(events) > 0
        assert "done" in event_types


async def test_chat_with_existing_conversation(
    client: AsyncClient, ready_document, conversation_with_messages
):
    mock_results = [
        SearchResult(
            chunk_id="c1",
            document_id=ready_document.id,
            chunk_index=0,
            content="Relevant text.",
            page_number=1,
            score=0.9,
        ),
    ]

    def mock_stream(*args, **kwargs):
        yield "Response."

    with (
        patch(
            "app.routers.chat.retrieve_chunks",
            new_callable=AsyncMock,
            return_value=mock_results,
        ),
        patch("app.routers.chat.stream_rag_response", side_effect=mock_stream),
    ):
        resp = await client.post(
            "/api/chat",
            json={
                "message": "Follow up question",
                "document_ids": [ready_document.id],
                "conversation_id": conversation_with_messages.id,
            },
        )
        assert resp.status_code == 200
        events = parse_sse_events(resp.text)
        event_types = [e["event"] for e in events if "event" in e]
        assert "done" in event_types


async def test_chat_conversation_not_found(client: AsyncClient, ready_document):
    resp = await client.post(
        "/api/chat",
        json={
            "message": "Hello",
            "document_ids": [ready_document.id],
            "conversation_id": "nonexistent-id",
        },
    )
    assert resp.status_code == 404


# --- LLM provider tests ---


def test_get_llm_provider_openai():
    with patch("app.services.llm.settings") as mock_settings:
        mock_settings.llm_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_chat_model = "gpt-4o-mini"
        with patch("openai.OpenAI"):
            from app.services.llm import get_llm_provider

            provider = get_llm_provider()
            assert provider.__class__.__name__ == "OpenAILLMProvider"


def test_get_llm_provider_anthropic():
    with patch("app.services.llm.settings") as mock_settings:
        mock_settings.llm_provider = "anthropic"
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.anthropic_chat_model = "claude-sonnet-4-20250514"
        with patch("anthropic.Anthropic"):
            from app.services.llm import get_llm_provider

            provider = get_llm_provider()
            assert provider.__class__.__name__ == "AnthropicLLMProvider"


def test_get_llm_provider_unknown():
    with patch("app.services.llm.settings") as mock_settings:
        mock_settings.llm_provider = "unknown"
        from app.services.llm import get_llm_provider

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider()


# --- Helper ---


def parse_sse_events(text: str) -> list[dict[str, str]]:
    """Parse SSE text into a list of event dicts."""
    events = []
    current: dict[str, str] = {}
    for line in text.split("\n"):
        if line.startswith("event:"):
            current["event"] = line[len("event:") :].strip()
        elif line.startswith("data:"):
            current["data"] = line[len("data:") :].strip()
        elif line == "" and current:
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events
