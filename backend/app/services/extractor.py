from dataclasses import dataclass

import docx
from pypdf import PdfReader


@dataclass
class PageContent:
    page_number: int
    content: str


def extract_text(file_path: str, file_type: str) -> list[PageContent]:
    """Extract text from a document file.

    Args:
        file_path: Path to the document file.
        file_type: File extension ("pdf" or "docx").

    Returns:
        List of PageContent with page numbers and text content.
    """
    if file_type == "pdf":
        return _extract_pdf(file_path)
    elif file_type == "docx":
        return _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_path: str) -> list[PageContent]:
    reader = PdfReader(file_path)
    pages: list[PageContent] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append(PageContent(page_number=i + 1, content=text))

    return pages


def _extract_docx(file_path: str) -> list[PageContent]:
    doc = docx.Document(file_path)
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
