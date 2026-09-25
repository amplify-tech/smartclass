"""Normalize extracted text and split it into overlapping RAG chunks."""
from __future__ import annotations

import re
from dataclasses import dataclass

_WHITESPACE_RE = re.compile(r'[ \t]+')
_MULTI_NEWLINE_RE = re.compile(r'\n{3,}')


@dataclass(frozen=True)
class TextChunk:
    """Ordered chunk ready for embedding / DocumentChunk persistence."""

    text: str
    page_number: int | None
    chunk_index: int


def normalize_text_for_rag(text: str) -> str:
    """Collapse noisy whitespace while keeping paragraph breaks."""
    if not text:
        return ''
    cleaned = text.replace('\r\n', '\n').replace('\r', '\n')
    cleaned = _WHITESPACE_RE.sub(' ', cleaned)
    cleaned = _MULTI_NEWLINE_RE.sub('\n\n', cleaned)
    return cleaned.strip()


def _validate_chunk_params(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError('chunk_size must be a positive integer.')
    if chunk_overlap < 0:
        raise ValueError('chunk_overlap must be >= 0.')
    if chunk_overlap >= chunk_size:
        raise ValueError('chunk_overlap must be smaller than chunk_size.')


def chunk_text_for_rag(
    text: str,
    *,
    page_number: int | None = None,
    chunk_size: int,
    chunk_overlap: int,
    start_index: int = 0,
) -> list[TextChunk]:
    """Split normalized text into overlapping character windows for RAG."""
    _validate_chunk_params(chunk_size, chunk_overlap)
    normalized = normalize_text_for_rag(text)
    if not normalized:
        return []

    chunks: list[TextChunk] = []
    start = 0
    length = len(normalized)
    index = start_index
    step = chunk_size - chunk_overlap

    while start < length:
        end = min(start + chunk_size, length)
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(
                TextChunk(
                    text=piece,
                    page_number=page_number,
                    chunk_index=index,
                ),
            )
            index += 1
        if end >= length:
            break
        start += step

    return chunks


def chunk_document_pages_for_rag(
    pages,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    """Chunk each extracted page with a global sequential index for RAG."""
    _validate_chunk_params(chunk_size, chunk_overlap)

    all_chunks: list[TextChunk] = []
    next_index = 0
    for page in pages:
        page_chunks = chunk_text_for_rag(
            page.text,
            page_number=page.page_number,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            start_index=next_index,
        )
        all_chunks.extend(page_chunks)
        next_index += len(page_chunks)

    return all_chunks
