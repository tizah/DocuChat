from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import NotFoundError
from app.models.chunk import Chunk
from app.models.document import Document
from app.schemas import ChunkWithContextResponse

router = APIRouter(prefix="/api/chunks", tags=["chunks"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/{chunk_id}", response_model=ChunkWithContextResponse)
async def get_chunk_with_context(chunk_id: str, db: DbSession, current_user: CurrentUser) -> dict:
    result = await db.execute(select(Chunk).where(Chunk.id == chunk_id))
    chunk = result.scalar_one_or_none()
    if not chunk:
        raise NotFoundError("Chunk not found")

    # Get document filename — also verifies user ownership
    doc_result = await db.execute(
        select(Document).where(
            Document.id == chunk.document_id, Document.user_id == current_user.id
        )
    )
    document = doc_result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Chunk not found")

    # Get previous chunk (chunk_index - 1)
    prev_result = await db.execute(
        select(Chunk).where(
            Chunk.document_id == chunk.document_id,
            Chunk.chunk_index == chunk.chunk_index - 1,
        )
    )
    prev_chunk = prev_result.scalar_one_or_none()

    # Get next chunk (chunk_index + 1)
    next_result = await db.execute(
        select(Chunk).where(
            Chunk.document_id == chunk.document_id,
            Chunk.chunk_index == chunk.chunk_index + 1,
        )
    )
    next_chunk = next_result.scalar_one_or_none()

    return {
        "chunk": chunk,
        "previous_chunk": prev_chunk,
        "next_chunk": next_chunk,
        "document_filename": document.filename,
    }
