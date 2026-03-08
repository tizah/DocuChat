from pathlib import Path

import pytest
from httpx import AsyncClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_upload_valid_pdf(client: AsyncClient, upload_dir: str):
    pdf_path = FIXTURES_DIR / "sample.pdf"
    with open(pdf_path, "rb") as f:
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["file_type"] == "pdf"
    assert data["status"] in ("uploaded", "extracted", "ready", "processing")
    assert data["size_bytes"] > 0
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_upload_valid_docx(client: AsyncClient, upload_dir: str):
    docx_path = FIXTURES_DIR / "sample.docx"
    with open(docx_path, "rb") as f:
        response = await client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "test.docx",
                    f,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.docx"
    assert data["file_type"] == "docx"
    assert data["status"] in ("extracted", "ready", "processing")


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, upload_dir: str):
    response = await client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["detail"]["code"] == "INVALID_FILE_TYPE"


@pytest.mark.asyncio
async def test_upload_oversized_file(client: AsyncClient, upload_dir: str):
    from app.config import settings

    original = settings.max_upload_size
    settings.max_upload_size = 100  # 100 bytes

    try:
        docx_path = FIXTURES_DIR / "sample.docx"
        with open(docx_path, "rb") as f:
            response = await client.post(
                "/api/documents/upload",
                files={
                    "file": (
                        "big.docx",
                        f,
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document",
                    )
                },
            )
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["code"] == "FILE_TOO_LARGE"
    finally:
        settings.max_upload_size = original


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, upload_dir: str):
    response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["documents"] == []


@pytest.mark.asyncio
async def test_list_documents_after_upload(client: AsyncClient, upload_dir: str):
    pdf_path = FIXTURES_DIR / "sample.pdf"
    with open(pdf_path, "rb") as f:
        await client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
        )

    response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["documents"][0]["filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_get_document(client: AsyncClient, upload_dir: str):
    pdf_path = FIXTURES_DIR / "sample.pdf"
    with open(pdf_path, "rb") as f:
        upload_resp = await client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
        )
    doc_id = upload_resp.json()["id"]

    response = await client.get(f"/api/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient):
    response = await client.get("/api/documents/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient, upload_dir: str):
    pdf_path = FIXTURES_DIR / "sample.pdf"
    with open(pdf_path, "rb") as f:
        upload_resp = await client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
        )
    doc_id = upload_resp.json()["id"]

    response = await client.delete(f"/api/documents/{doc_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/documents/{doc_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_not_found(client: AsyncClient):
    response = await client.delete("/api/documents/nonexistent-id")
    assert response.status_code == 404
