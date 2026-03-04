from dataclasses import dataclass

import tiktoken

from app.config import settings
from app.services.extractor import PageContent

_encoding = tiktoken.get_encoding("cl100k_base")


@dataclass
class ChunkData:
    document_id: str
    chunk_index: int
    page_number: int
    content: str
    token_count: int


def count_tokens(text: str) -> int:
    return len(_encoding.encode(text))


def chunk_pages(
    pages: list[PageContent],
    document_id: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[ChunkData]:
    """Split extracted pages into overlapping chunks sized by token count.

    Uses recursive character splitting: tries to split on paragraph breaks first,
    then sentence boundaries, then word boundaries, preserving semantic units.
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap

    separators = ["\n\n", "\n", ". ", " "]
    chunks: list[ChunkData] = []
    chunk_index = 0

    for page in pages:
        text = page.content.strip()
        if not text:
            continue

        splits = _recursive_split(text, separators, chunk_size)

        # Merge small splits and apply overlap
        current_chunk = ""
        for split in splits:
            candidate = f"{current_chunk} {split}".strip() if current_chunk else split

            if count_tokens(candidate) <= chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(ChunkData(
                        document_id=document_id,
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        content=current_chunk,
                        token_count=count_tokens(current_chunk),
                    ))
                    chunk_index += 1

                    # Apply overlap: keep tail tokens from the previous chunk
                    overlap_text = _get_overlap(current_chunk, chunk_overlap)
                    current_chunk = f"{overlap_text} {split}".strip() if overlap_text else split
                else:
                    # Single split exceeds chunk_size — emit it as-is
                    chunks.append(ChunkData(
                        document_id=document_id,
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        content=split,
                        token_count=count_tokens(split),
                    ))
                    chunk_index += 1
                    current_chunk = ""

        if current_chunk:
            chunks.append(ChunkData(
                document_id=document_id,
                chunk_index=chunk_index,
                page_number=page.page_number,
                content=current_chunk,
                token_count=count_tokens(current_chunk),
            ))
            chunk_index += 1

    return chunks


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Recursively split text by trying each separator in order."""
    if count_tokens(text) <= chunk_size:
        return [text]

    for sep in separators:
        parts = text.split(sep)
        if len(parts) > 1:
            result: list[str] = []
            for part in parts:
                stripped = part.strip()
                if not stripped:
                    continue
                if count_tokens(stripped) <= chunk_size:
                    result.append(stripped)
                else:
                    # Try finer separators on this part
                    remaining_seps = separators[separators.index(sep) + 1 :]
                    if remaining_seps:
                        result.extend(_recursive_split(stripped, remaining_seps, chunk_size))
                    else:
                        result.append(stripped)
            return result

    # No separator worked — return text as-is
    return [text]


def _get_overlap(text: str, overlap_tokens: int) -> str:
    """Get the last `overlap_tokens` tokens from text as a string."""
    tokens = _encoding.encode(text)
    if len(tokens) <= overlap_tokens:
        return text
    overlap = tokens[-overlap_tokens:]
    return _encoding.decode(overlap)
