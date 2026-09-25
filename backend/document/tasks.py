"""Background handlers for document app jobs (kwargs = Job.payload)."""
import logging

from common.exceptions import TaskFailed

logger = logging.getLogger(__name__)

_GENERIC_ERROR = 'Document processing failed. Please try again.'


def process_document_for_rag(*, job_id, document_id, **chunk_opts):
    """Background handler for PROCESS_DOCUMENT."""
    from document.models import Document
    from document.services import (
        DocumentProcessingError,
        DocumentProcessingService,
        EmbeddingError,
    )

    logger.info(
        'process_document_for_rag job_id=%s document_id=%s',
        job_id,
        document_id,
    )
    try:
        return DocumentProcessingService().process_document_for_rag(
            document_id,
            **chunk_opts,
        )
    except Document.DoesNotExist as exc:
        raise TaskFailed(_GENERIC_ERROR) from exc
    except (DocumentProcessingError, EmbeddingError) as exc:
        raise TaskFailed(str(exc).strip() or _GENERIC_ERROR) from exc
