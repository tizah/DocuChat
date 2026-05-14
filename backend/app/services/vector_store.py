"""Vector similarity search via pgvector.

Embeddings live on the `chunks` table — there is no separate vector store.
This module exposes the search function plus the `SearchResult` dataclass
that the RAG and chat layers consume.
"""

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    chunk_index: int
    page_number: int
    content: str
    score: float


async def search_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    document_ids: list[str],
    top_k: int = 5,
) -> list[SearchResult]:
    """Return the top_k chunks across `document_ids` ranked by cosine similarity.

    Uses pgvector's `<=>` cosine distance operator (range [0, 2], 0 = identical).
    Converts to a 0-1 similarity score to match the previous Chroma-based API.
    """
    if not document_ids:
        return []

    distance = Chunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(Chunk, distance.label("distance"))
        .where(Chunk.document_id.in_(document_ids))
        .where(Chunk.embedding.is_not(None))
        .order_by(distance.asc())
        .limit(top_k)
    )
    result = await db.execute(stmt)

    return [
        SearchResult(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            content=chunk.content,
            score=1.0 - (dist / 2.0),
        )
        for chunk, dist in result.all()
    ]
