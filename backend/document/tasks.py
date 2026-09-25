"""Synchronous task helpers for the document app."""
import logging

from document.services import DocumentProcessingService

logger = logging.getLogger(__name__)


def process_document_for_rag(document_id: int, **chunk_opts):
    """Extract and chunk a stored document for RAG (embeddings come later)."""
    logger.info('process_document_for_rag started document_id=%s', document_id)
    chunks = DocumentProcessingService().process_document_for_rag(
        document_id,
        **chunk_opts,
    )
    return {
        'document_id': document_id,
        'status': 'ready',
        'chunk_count': len(chunks),
    }
