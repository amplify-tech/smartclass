"""Execute a Job on the shared executor and persist status/result/error."""

import logging

from django.db import close_old_connections
from django.utils import timezone

from common.constants import GENERATE_QUESTIONS, MAX_RETRIES, PROCESS_DOCUMENT_FOR_RAG
from common.exceptions import TaskFailed
from document.tasks import process_document_for_rag
from exam.tasks import generate_questions
from .models import Job

logger = logging.getLogger(__name__)

TASK_HANDLER_MAPPING = {
    GENERATE_QUESTIONS: generate_questions,
    PROCESS_DOCUMENT_FOR_RAG: process_document_for_rag,
}

_GENERIC_TASK_ERROR = 'Task failed. Please try again.'


class JobAuthorizationError(PermissionError):
    """Raised when request_user_id does not match Job.created_by_id."""


def run_job(job_id, request_user_id=None):
    """Worker entrypoint"""
    close_old_connections()

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        logger.error('run_job missing job_id=%s', job_id)
        return

    if job.status in (Job.Status.RUNNING, Job.Status.COMPLETED):
        logger.info('job_id=%s already %s', job_id, job.status)
        return

    if job.retry_count >= MAX_RETRIES:
        logger.error('job_id=%s reached max retries', job_id)
        return

    try:
        _assert_job_owner(job, request_user_id)

        job.status = Job.Status.RUNNING
        job.started_at = timezone.now()
        job.error = ''
        job.save(update_fields=['status', 'started_at', 'error'])

        handler = TASK_HANDLER_MAPPING.get(job.task_type)
        if not handler:
            logger.error('unknown task_type=%s job_id=%s', job.task_type, job_id)
            raise TaskFailed(_GENERIC_TASK_ERROR)

        result = handler(job_id=job.id, **(job.payload or {}))

        job.status = Job.Status.COMPLETED
        job.result = result
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'result', 'completed_at'])
        logger.info('job_id=%s completed task_type=%s', job_id, job.task_type)

    except JobAuthorizationError as exc:
        job.status = Job.Status.FAILED
        job.error = _GENERIC_TASK_ERROR
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error', 'completed_at'])
        logger.warning('job_id=%s auth failed: %s', job_id, exc)

    except TaskFailed as exc:
        job.status = Job.Status.FAILED
        job.error = exc.user_message
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error', 'completed_at'])
        logger.warning('job_id=%s failed safely: %s', job_id, exc.user_message)

    except Exception:
        job.status = Job.Status.FAILED
        job.error = _GENERIC_TASK_ERROR
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error', 'completed_at'])
        logger.exception('job_id=%s failed', job_id)

    finally:
        close_old_connections()


def _assert_job_owner(job, request_user_id):
    """Background auth: submitter must match Job.created_by (both may be None)."""
    owner_id = job.created_by_id
    if owner_id != request_user_id:
        raise JobAuthorizationError(
            f'Job {job.id} owner mismatch: '
            f'created_by_id={owner_id} request_user_id={request_user_id}'
        )
