"""Document extract + chunk orchestration for the RAG pipeline (Step 2).

Embeddings and retrieval are intentionally out of scope here.
"""
import logging
from pathlib import Path

from django.db import transaction

from common.constants import RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE
from document.models import Document, DocumentChunk
from document.utils.extractors import FileExtractionError, extract_pages
from document.utils.rag_text_chunker import chunk_document_pages_for_rag

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Raised when extract/chunk fails for a stored document."""


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
