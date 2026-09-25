"""Document extract/chunk (Step 2) and embedding (Step 3) for the RAG pipeline.

Retrieval and RAG generation are intentionally out of scope here.
"""
import logging
from dataclasses import dataclass
from pathlib import Path

import requests
from django.db import transaction

from common.constants import (
    EMBEDDING_DIMENSIONS,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_EMBEDDING_BATCH_SIZE,
)
from common.llm.factory import get_llm_provider
from document.models import Document, DocumentChunk
from document.utils.extractors import FileExtractionError, extract_pages
from document.utils.rag_text_chunker import chunk_document_pages_for_rag

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Raised when extract/chunk fails for a stored document."""


class EmbeddingError(Exception):
    """Raised when embedding generation or persistence fails."""


@dataclass(frozen=True)
class EmbeddingResult:
    """Vectors plus the model id that produced them."""

    vectors: list
    model: str


class DocumentProcessingService:
    """Read a stored file, extract text via type strategies, and produce RAG chunks."""

    def extract_and_chunk_for_rag(
        self,
        document,
        *,
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
    ):
        """Extract text and return ordered chunks (no DB writes)."""
        data = self._read_file_bytes(document)
        filename = Path(document.file.name).name if document.file else ''
        try:
            pages = extract_pages(data, filename=filename)
        except FileExtractionError as exc:
            raise DocumentProcessingError(str(exc)) from exc

        chunks = chunk_document_pages_for_rag(
            pages,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        if not chunks:
            raise DocumentProcessingError(
                'File produced no extractable text after normalization.',
            )
        return chunks

    def process_document_for_rag(
        self,
        document_id,
        *,
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
    ):
        """Extract, chunk, replace stored chunks, and update document status."""
        try:
            document = Document.objects.get(pk=document_id)
            document.status = Document.Status.PROCESSING
            document.save(update_fields=['status', 'updated_at'])

            chunks = self.extract_and_chunk_for_rag(
                document,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            with transaction.atomic():
                document.chunks.all().delete()
                DocumentChunk.objects.bulk_create(
                    [
                        DocumentChunk(
                            document=document,
                            text=chunk.text,
                            page_number=chunk.page_number,
                            chunk_index=chunk.chunk_index,
                        )
                        for chunk in chunks
                    ],
                )
                document.status = Document.Status.READY
                document.save(update_fields=['status', 'updated_at'])

            logger.info(
                'Document processed for RAG document_id=%s chunks=%s',
                document_id,
                len(chunks),
            )
            return chunks
        except DocumentProcessingError:
            Document.objects.filter(pk=document_id).update(
                status=Document.Status.FAILED,
            )
            raise
        except Exception as exc:
            Document.objects.filter(pk=document_id).update(
                status=Document.Status.FAILED,
            )
            logger.exception(
                'Unexpected error processing document_id=%s for RAG',
                document_id,
            )
            raise DocumentProcessingError(
                'Document processing failed unexpectedly.',
            ) from exc

    @staticmethod
    def _read_file_bytes(document):
        if not document.file:
            raise DocumentProcessingError('Document has no file attached.')

        try:
            with document.file.open('rb') as handle:
                data = handle.read()
        except Exception as exc:
            raise DocumentProcessingError(
                f'Could not read document file from storage: {exc}',
            ) from exc

        if not data:
            raise DocumentProcessingError('Document file is empty.')
        return data


class EmbeddingService:
    """Generate 768-dim embeddings via LLMProvider and optionally persist them."""

    def __init__(self, provider=None):
        self._provider = provider or get_llm_provider()

    def embed_texts(self, texts, *, batch_size=RAG_EMBEDDING_BATCH_SIZE):
        """Embed texts in batches; return vectors and the embedding model name."""
        if not texts:
            raise EmbeddingError('No texts to embed.')
        if batch_size <= 0:
            raise EmbeddingError('batch_size must be a positive integer.')

        model = self._provider.embedding_model
        vectors = []
        try:
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]
                batch_vectors = self._provider.embed(batch)
                self._validate_vectors(batch_vectors, expected_count=len(batch))
                vectors.extend(batch_vectors)
        except EmbeddingError:
            raise
        except requests.RequestException as exc:
            logger.exception('Embedding provider HTTP error model=%s', model)
            raise EmbeddingError('Embedding provider request failed.') from exc
        except (ValueError, TypeError, KeyError) as exc:
            logger.exception('Embedding provider error model=%s', model)
            raise EmbeddingError('Embedding provider returned an invalid result.') from exc

        logger.info(
            'Embedded texts count=%s model=%s dims=%s',
            len(vectors),
            model,
            EMBEDDING_DIMENSIONS,
        )
        return EmbeddingResult(vectors=vectors, model=model)

    def embed_chunks(self, chunks, *, batch_size=RAG_EMBEDDING_BATCH_SIZE):
        """Embed DocumentChunk rows and store embedding + embedding_model."""
        chunks = list(chunks)
        if not chunks:
            raise EmbeddingError('No chunks to embed.')

        result = self.embed_texts(
            [chunk.text for chunk in chunks],
            batch_size=batch_size,
        )
        for chunk, vector in zip(chunks, result.vectors):
            chunk.embedding = vector
            chunk.embedding_model = result.model

        DocumentChunk.objects.bulk_update(
            chunks,
            ['embedding', 'embedding_model', 'updated_at'],
        )
        logger.info(
            'Stored chunk embeddings count=%s model=%s',
            len(chunks),
            result.model,
        )
        return result

    @staticmethod
    def _validate_vectors(vectors, *, expected_count):
        if not isinstance(vectors, list) or len(vectors) != expected_count:
            raise EmbeddingError(
                f'Expected {expected_count} embedding vectors, '
                f'got {len(vectors) if isinstance(vectors, list) else type(vectors)}.',
            )
        for index, vector in enumerate(vectors):
            if not isinstance(vector, (list, tuple)):
                raise EmbeddingError(f'Embedding at index {index} is not a vector.')
            if len(vector) != EMBEDDING_DIMENSIONS:
                raise EmbeddingError(
                    f'Embedding at index {index} has {len(vector)} dims; '
                    f'expected {EMBEDDING_DIMENSIONS}.',
                )
