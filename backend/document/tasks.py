"""Background tasks for the document app.

Example usage from a service or view:

    from document.tasks import process_document

    process_document.delay(document_id)
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, document_id: int):
    """Placeholder for async document processing (parse, embed, etc.)."""
    logger.info('process_document started document_id=%s', document_id)
    # TODO: call document service layer here
    return {'document_id': document_id, 'status': 'ok'}
