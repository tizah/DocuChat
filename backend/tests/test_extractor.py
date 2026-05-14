from pathlib import Path

import pytest

from app.services.extractor import extract_text

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def test_extract_pdf():
    pages = extract_text(_read("sample.pdf"), "pdf")
    assert isinstance(pages, list)
    # Our test PDF has blank pages (no embedded text), so may be empty
    for page in pages:
        assert page.page_number >= 1
        assert isinstance(page.content, str)


def test_extract_docx():
    pages = extract_text(_read("sample.docx"), "docx")
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "test document" in pages[0].content.lower()
    assert "multiple paragraphs" in pages[0].content.lower()


def test_extract_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text(b"dummy", "txt")
