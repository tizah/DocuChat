import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import NotFoundError, ValidationError
from app.models.chunk import Chunk
from app.models.document import Document
from app.schemas import (
    ChunkListResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
)
from app.services.pipeline import process_document
from app.services.storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def _run_pipeline_background(doc_id: str, storage_key: str, file_ext: str) -> None:
    """Wrapper to run the pipeline in background, catching exceptions."""
    from app.database import async_session

    try:
        async with async_session() as db:
            await process_document(doc_id, storage_key, file_ext, db)
            await db.commit()
    except Exception:
        logger.exception("Background pipeline failed for document %s", doc_id)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(file: UploadFile, db: DbSession, current_user: CurrentUser) -> Document:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"File type '{file.content_type}' is not supported. Upload PDF or DOCX files only.",
            code="INVALID_FILE_TYPE",
        )

    content = await file.read()
    max_mb = settings.max_upload_size // (1024 * 1024)
    if len(content) > settings.max_upload_size:
        raise ValidationError(
            f"File size exceeds the {max_mb}MB limit.",
            code="FILE_TOO_LARGE",
        )

    doc_id = str(uuid.uuid4())
    file_ext = ALLOWED_MIME_TYPES[file.content_type]
    storage_key = f"{doc_id}.{file_ext}"

    # S3/R2 PutObject is blocking; offload so it doesn't stall the event loop.
    await asyncio.to_thread(get_storage().save, storage_key, content)

    document = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename or "untitled",
        file_type=file_ext,
        size_bytes=len(content),
        status="processing",
    )
    db.add(document)
    await db.flush()
    await db.commit()
    await db.refresh(document)

    # Run pipeline in background so upload returns immediately
    asyncio.create_task(_run_pipeline_background(doc_id, storage_key, file_ext))

    return document


@router.get("", response_model=DocumentListResponse)
async def list_documents(db: DbSession, current_user: CurrentUser) -> dict:
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    documents = list(result.scalars().all())
    return {"documents": documents, "total": len(documents)}


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: DbSession, current_user: CurrentUser) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document not found")
    return document


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str, db: DbSession, current_user: CurrentUser
) -> dict:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document not found")

    chunk_count = 0
    if document.status in ("ready", "embedding", "chunking"):
        chunk_result = await db.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunk_count = len(list(chunk_result.scalars().all()))

    return {
        "id": document.id,
        "status": document.status,
        "error_message": document.error_message,
        "page_count": document.page_count,
        "chunk_count": chunk_count,
    }


@router.get("/{document_id}/chunks", response_model=ChunkListResponse)
async def list_document_chunks(
    document_id: str,
    db: DbSession,
    current_user: CurrentUser,
    page: int | None = None,
) -> dict:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document not found")

    query = select(Chunk).where(Chunk.document_id == document_id)
    if page is not None:
        query = query.where(Chunk.page_number == page)
    query = query.order_by(Chunk.chunk_index)

    chunk_result = await db.execute(query)
    chunks = list(chunk_result.scalars().all())
    return {"chunks": chunks, "total": len(chunks), "document_id": document_id}


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, db: DbSession, current_user: CurrentUser) -> None:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document not found")

    # Chunks (and their embeddings) cascade with the document via ON DELETE CASCADE.

    # Delete file from storage (best-effort — don't block the row delete on this)
    try:
        get_storage().delete(f"{document.id}.{document.file_type}")
    except Exception:
        logger.warning("Storage delete failed for document %s", document.id, exc_info=True)

    await db.delete(document)
