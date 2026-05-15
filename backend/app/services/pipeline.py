import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chunker import chunk_pages
from app.services.embedder import get_embedding_provider
from app.services.extractor import extract_text
from app.services.storage import get_storage

logger = logging.getLogger(__name__)


async def process_document(
    document_id: str,
    storage_key: str,
    file_type: str,
    db: AsyncSession,
) -> None:
    """Run the full processing pipeline: extract → chunk → embed → store vectors.

    Updates document status at each stage. On failure, sets status to "failed"
    with an error message.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        logger.error("Document %s not found", document_id)
        return

    try:
        logger.info("Starting pipeline for document %s", document_id)

        # Stage 1: Extract
        document.status = "extracting"
        await db.flush()

        file_data = get_storage().read(storage_key)
        pages = extract_text(file_data, file_type)
        document.page_count = len(pages)
        logger.info("Extraction complete for document %s: %d pages", document_id, len(pages))

        if not pages:
            document.status = "failed"
            document.error_message = "No text content could be extracted from the document."
            await db.flush()
            return

        # Stage 2: Chunk
        document.status = "chunking"
        await db.flush()

        chunks = chunk_pages(pages, document_id)
        logger.info("Chunking complete for document %s: %d chunks", document_id, len(chunks))

        # Store chunks in the database
        db_chunks: list[Chunk] = []
        for chunk in chunks:
            db_chunk = Chunk(
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                content=chunk.content,
                token_count=chunk.token_count,
            )
            db.add(db_chunk)
            db_chunks.append(db_chunk)
        await db.flush()

        # Stage 3: Embed — write vectors back onto each chunk row.
        # pgvector indexes the column; no separate store to keep in sync.
        document.status = "embedding"
        await db.flush()

        provider = get_embedding_provider()
        texts = [c.content for c in chunks]
        embeddings = await provider.embed(texts)
        for db_chunk, vec in zip(db_chunks, embeddings, strict=True):
            db_chunk.embedding = vec
        await db.flush()
        logger.info("Embedding complete for document %s", document_id)

        document.status = "ready"
        await db.flush()
        logger.info(
            "Pipeline finished for document %s: %d pages, %d chunks",
            document_id,
            len(pages),
            len(chunks),
        )

    except Exception as e:
        logger.exception("Failed to process document %s", document_id)
        document.status = "failed"
        document.error_message = str(e)
        await db.flush()
