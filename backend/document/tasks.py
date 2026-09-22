"""Synchronous task helpers for the document app.

Example usage from a service or view:

    from document.tasks import process_document

    process_document(document_id)
"""
import logging

logger = logging.getLogger(__name__)


def process_document(document_id: int):
    """Placeholder for document processing (parse, embed, etc.)."""
    logger.info('process_document started document_id=%s', document_id)
    # TODO: call document service layer here
    return {'document_id': document_id, 'status': 'ok'}
