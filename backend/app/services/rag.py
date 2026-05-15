import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.services.embedder import get_embedding_provider
from app.services.llm import get_llm_provider
from app.services.vector_store import SearchResult, search_chunks

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are DocuChat, an AI assistant that answers questions "
    "based on uploaded documents.\n\n"
    "IMPORTANT RULES:\n"
    "1. Answer ONLY based on the provided document context below. "
    "Do not use prior knowledge.\n"
    "2. When referencing information from the documents, ALWAYS cite "
    "the source inline using the format: [Source: filename, Page X]\n"
    "3. If the provided context does not contain enough information "
    'to answer the question, say: "I don\'t have enough information '
    'in the provided documents to answer this."\n'
    "4. Be concise, accurate, and helpful.\n"
    "5. If multiple documents contain relevant information, "
    "synthesize them and cite each source.\n\n"
    "DOCUMENT CONTEXT:\n"
    "{context}"
)


@dataclass
class SourceChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    content: str
    score: float


def build_context(
    search_results: list[SearchResult],
    filename_map: dict[str, str],
) -> tuple[str, list[SourceChunk]]:
    """Build the context string and source chunk list from search results."""
    context_parts: list[str] = []
    source_chunks: list[SourceChunk] = []

    for result in search_results:
        filename = filename_map.get(result.document_id, "Unknown")
        context_parts.append(
            f"[Document: {filename}, Page {result.page_number}]\n{result.content}\n"
        )
        source_chunks.append(SourceChunk(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            filename=filename,
            page_number=result.page_number,
            content=result.content,
            score=result.score,
        ))

    return "\n---\n".join(context_parts), source_chunks


async def get_filename_map(
    document_ids: list[str], db: AsyncSession
) -> dict[str, str]:
    """Get a mapping of document_id → filename."""
    result = await db.execute(
        select(Document).where(Document.id.in_(document_ids))
    )
    return {doc.id: doc.filename for doc in result.scalars().all()}


async def stream_rag_response(
    query: str,
    search_results: list[SearchResult],
    filename_map: dict[str, str],
    conversation_history: list[dict[str, str]] | None = None,
) -> AsyncIterator[str]:
    """Stream a RAG response from the LLM."""
    context, _source_chunks = build_context(search_results, filename_map)
    system_prompt = SYSTEM_PROMPT.format(context=context)

    messages: list[dict[str, str]] = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": query})

    llm = get_llm_provider()
    async for token in llm.stream_chat(system_prompt, messages):
        yield token


async def retrieve_chunks(
    db: AsyncSession,
    query: str,
    document_ids: list[str],
    top_k: int = 5,
) -> list[SearchResult]:
    """Embed the query and retrieve relevant chunks via pgvector."""
    embedder = get_embedding_provider()
    query_embedding = await embedder.embed_query(query)

    return await search_chunks(
        db=db,
        query_embedding=query_embedding,
        document_ids=document_ids,
        top_k=top_k,
    )
