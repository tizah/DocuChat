from unittest.mock import MagicMock, patch

import pytest

from app.services.embedder import BATCH_SIZE, OpenAIEmbeddingProvider, get_embedding_provider


def _make_mock_response(n: int, dims: int = 1536):
    """Create a mock OpenAI embeddings response."""
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[0.1] * dims, index=i) for i in range(n)
    ]
    return mock_response


@patch("openai.OpenAI")
def test_embed_single_text(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.embeddings.create.return_value = _make_mock_response(1)

    provider = OpenAIEmbeddingProvider()
    result = provider.embed(["hello world"])

    assert len(result) == 1
    assert len(result[0]) == 1536
    mock_client.embeddings.create.assert_called_once()


@patch("openai.OpenAI")
def test_embed_batch_processing(mock_openai_class):
    """Verify texts are processed in batches of BATCH_SIZE."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    n_texts = BATCH_SIZE + 50  # Should require 2 batches
    texts = [f"text {i}" for i in range(n_texts)]

    mock_client.embeddings.create.side_effect = [
        _make_mock_response(BATCH_SIZE),
        _make_mock_response(50),
    ]

    provider = OpenAIEmbeddingProvider()
    result = provider.embed(texts)

    assert len(result) == n_texts
    assert mock_client.embeddings.create.call_count == 2


@patch("openai.OpenAI")
def test_embed_query(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.embeddings.create.return_value = _make_mock_response(1)

    provider = OpenAIEmbeddingProvider()
    result = provider.embed_query("test query")

    assert len(result) == 1536


@patch("openai.OpenAI")
def test_embed_retry_on_failure(mock_openai_class):
    """Verify retry logic on transient failures."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    mock_client.embeddings.create.side_effect = [
        ConnectionError("timeout"),
        ConnectionError("timeout"),
        _make_mock_response(1),
    ]

    provider = OpenAIEmbeddingProvider()
    result = provider.embed(["hello"])

    assert len(result) == 1
    assert mock_client.embeddings.create.call_count == 3


@patch("openai.OpenAI")
def test_embed_exhausted_retries(mock_openai_class):
    """After 3 failures, the error should propagate."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.embeddings.create.side_effect = ConnectionError("persistent failure")

    provider = OpenAIEmbeddingProvider()
    with pytest.raises(ConnectionError):
        provider.embed(["hello"])


def test_get_embedding_provider_openai():
    with patch("app.services.embedder.settings") as mock_settings:
        mock_settings.embedding_provider = "openai"
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        with patch("openai.OpenAI"):
            provider = get_embedding_provider()
            assert isinstance(provider, OpenAIEmbeddingProvider)


def test_get_embedding_provider_unknown():
    with patch("app.services.embedder.settings") as mock_settings:
        mock_settings.embedding_provider = "unknown"
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            get_embedding_provider()
