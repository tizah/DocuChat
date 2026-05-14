import io
from dataclasses import dataclass

import docx
from pypdf import PdfReader


@dataclass
class PageContent:
    page_number: int
    content: str


def extract_text(file_data: bytes, file_type: str) -> list[PageContent]:
    """Extract text from document bytes.

    Args:
        file_data: Raw bytes of the document.
        file_type: File extension ("pdf" or "docx").

    Returns:
        List of PageContent with page numbers and text content.
    """
    if file_type == "pdf":
        return _extract_pdf(file_data)
    elif file_type == "docx":
        return _extract_docx(file_data)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_data: bytes) -> list[PageContent]:
    reader = PdfReader(io.BytesIO(file_data))
    pages: list[PageContent] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append(PageContent(page_number=i + 1, content=text))

    return pages


def _extract_docx(file_data: bytes) -> list[PageContent]:
    doc = docx.Document(io.BytesIO(file_data))
    paragraphs: list[str] = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)

    # DOCX doesn't have native page numbers, so we group paragraphs as a single "page"
    if not paragraphs:
        return []

    combined_text = "\n\n".join(paragraphs)
    return [PageContent(page_number=1, content=combined_text)]
