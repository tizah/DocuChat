import os
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.document import Document
from app.schemas import DocumentListResponse, DocumentResponse
from app.services.extractor import extract_text

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(file: UploadFile, db: DbSession) -> Document:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": f"File type '{file.content_type}' is not supported. "
                "Upload PDF or DOCX files only.",
            },
        )

    content = await file.read()
    max_mb = settings.max_upload_size // (1024 * 1024)
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"File size exceeds the {max_mb}MB limit.",
            },
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = str(uuid.uuid4())
    file_ext = ALLOWED_MIME_TYPES[file.content_type]
    file_path = upload_dir / f"{doc_id}.{file_ext}"

    with open(file_path, "wb") as f:
        f.write(content)

    document = Document(
        id=doc_id,
        filename=file.filename or "untitled",
        file_type=file_ext,
        size_bytes=len(content),
        status="uploaded",
    )
    db.add(document)
    await db.flush()

    try:
        pages = extract_text(str(file_path), file_ext)
        document.status = "extracted"
        document.page_count = len(pages)
    except Exception as e:
        document.status = "failed"
        document.error_message = str(e)

    await db.flush()
    await db.refresh(document)
    return document


@router.get("", response_model=DocumentListResponse)
async def list_documents(db: DbSession) -> dict:
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    documents = list(result.scalars().all())
    return {"documents": documents, "total": len(documents)}


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: DbSession) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Document not found."},
        )
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, db: DbSession) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Document not found."},
        )

    upload_dir = Path(settings.upload_dir)
    file_path = upload_dir / f"{document.id}.{document.file_type}"
    if file_path.exists():
        os.remove(file_path)

    await db.delete(document)
