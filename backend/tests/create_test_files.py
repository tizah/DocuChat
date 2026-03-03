"""Helper script to create test fixture files."""

from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfWriter


def create_test_pdf(path: str, pages: list[str] | None = None) -> None:
    """Create a simple test PDF with text content."""
    if pages is None:
        pages = ["This is page one of a test PDF document.", "This is page two."]

    writer = PdfWriter()
    for _text in pages:
        writer.add_blank_page(width=612, height=792)
        page = writer.pages[-1]
        # Add text annotation as a simple way to add searchable text
        page.merge_page(page)

    writer.write(path)


def create_test_docx(path: str, paragraphs: list[str] | None = None) -> None:
    """Create a simple test DOCX with text content."""
    if paragraphs is None:
        paragraphs = [
            "This is a test document.",
            "It contains multiple paragraphs for testing.",
            "DocuChat should be able to extract this text.",
        ]

    doc = DocxDocument()
    for para in paragraphs:
        doc.add_paragraph(para)
    doc.save(path)


if __name__ == "__main__":
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    create_test_pdf(str(fixtures_dir / "sample.pdf"))
    create_test_docx(str(fixtures_dir / "sample.docx"))
    print("Test fixtures created.")
