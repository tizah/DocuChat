import asyncio
import logging
from abc import ABC, abstractmethod
from functools import lru_cache

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return their vector representations."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query text."""


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _call_api(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            logger.info("Embedding batch %d-%d of %d", i, i + len(batch), len(texts))
            embeddings = self._call_api(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self._embed_sync, texts)

    async def embed_query(self, text: str) -> list[float]:
        result = await asyncio.to_thread(self._call_api, [text])
        return result[0]


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    else:
        raise ValueError(
            f"Unknown embedding provider: '{provider}'. Supported: 'openai'."
        )
