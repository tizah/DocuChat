from app.services.chunker import ChunkData, chunk_pages, count_tokens
from app.services.extractor import PageContent


def test_count_tokens():
    assert count_tokens("hello world") > 0
    assert count_tokens("") == 0


def test_chunk_single_short_page():
    """A short page should produce a single chunk."""
    pages = [PageContent(page_number=1, content="This is a short document.")]
    chunks = chunk_pages(pages, "doc-1", chunk_size=100, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0].document_id == "doc-1"
    assert chunks[0].chunk_index == 0
    assert chunks[0].page_number == 1
    assert chunks[0].content == "This is a short document."
    assert chunks[0].token_count == count_tokens("This is a short document.")


def test_chunk_long_text_produces_multiple_chunks():
    """A long text should be split into multiple chunks."""
    # Create text that's definitely longer than 50 tokens
    long_text = "This is a sentence about testing. " * 50
    pages = [PageContent(page_number=1, content=long_text)]
    chunks = chunk_pages(pages, "doc-2", chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.document_id == "doc-2"
        assert chunk.page_number == 1
        assert chunk.token_count > 0
        assert len(chunk.content) > 0


def test_chunk_preserves_page_numbers():
    """Chunks from different pages should preserve their page numbers."""
    pages = [
        PageContent(page_number=1, content="Content from page one."),
        PageContent(page_number=2, content="Content from page two."),
    ]
    chunks = chunk_pages(pages, "doc-3", chunk_size=100, chunk_overlap=10)
    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2


def test_chunk_indices_are_sequential():
    """Chunk indices should be sequential across all pages."""
    pages = [
        PageContent(page_number=1, content="First page content."),
        PageContent(page_number=2, content="Second page content."),
        PageContent(page_number=3, content="Third page content."),
    ]
    chunks = chunk_pages(pages, "doc-4", chunk_size=100, chunk_overlap=10)
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i


def test_chunk_metadata_types():
    """Verify metadata types in ChunkData."""
    pages = [PageContent(page_number=1, content="Some content here.")]
    chunks = chunk_pages(pages, "doc-5", chunk_size=100, chunk_overlap=10)
    chunk = chunks[0]
    assert isinstance(chunk, ChunkData)
    assert isinstance(chunk.document_id, str)
    assert isinstance(chunk.chunk_index, int)
    assert isinstance(chunk.page_number, int)
    assert isinstance(chunk.content, str)
    assert isinstance(chunk.token_count, int)


def test_chunk_overlap_creates_continuity():
    """With overlap, consecutive chunks should share some content."""
    long_text = ". ".join([f"Sentence number {i} is here" for i in range(100)])
    pages = [PageContent(page_number=1, content=long_text)]
    chunks = chunk_pages(pages, "doc-6", chunk_size=30, chunk_overlap=10)

    if len(chunks) > 1:
        # Verify overlap exists by checking that consecutive chunks share some words
        for i in range(len(chunks) - 1):
            current_words = set(chunks[i].content.split())
            next_words = set(chunks[i + 1].content.split())
            # There should be some overlap in words
            assert len(current_words & next_words) > 0


def test_empty_pages_produce_no_chunks():
    """Empty pages should be skipped."""
    pages = [PageContent(page_number=1, content=""), PageContent(page_number=2, content="  ")]
    chunks = chunk_pages(pages, "doc-7", chunk_size=100, chunk_overlap=10)
    assert len(chunks) == 0
