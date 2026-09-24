"""Execute a Job on the shared executor and persist status/result/error."""

import logging

from django.db import close_old_connections
from django.utils import timezone

from common.constants import MAX_RETRIES
from exam.tasks import generate_questions
from .models import Job

logger = logging.getLogger(__name__)

TASK_HANDLER_MAPPING = {
    'GENERATE_QUESTIONS': generate_questions,
}


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

    if job.status in [ Job.Status.RUNNING, Job.Status.COMPLETED]:
        logger.info(f'job_id={job_id} already {job.status.value}')
        return

    if job.retry_count >= MAX_RETRIES:
        logger.error(f'job_id={job_id} reached max retries')
        return

    try:
        _assert_job_owner(job, request_user_id)

        job.status = Job.Status.RUNNING
        job.started_at = timezone.now()
        job.error = ''
        job.save(update_fields=['status', 'started_at', 'error'])

        handler = TASK_HANDLER_MAPPING.get(job.task_type)
        if not handler:
            raise ValueError(f'Unknown task type: {job.task_type}')

        result = handler(**(job.payload or {}))

        job.status = Job.Status.COMPLETED
        job.result = result
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'result', 'completed_at'])
        logger.info('job_id=%s completed task_type=%s', job_id, job.task_type)

    except JobAuthorizationError as exc:
        job.status = Job.Status.FAILED
        job.error = str(exc)
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error', 'completed_at'])
        logger.warning('job_id=%s auth failed: %s', job_id, exc)

    except Exception as exc:
        job.status = Job.Status.FAILED
        job.error = str(exc)
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'error', 'completed_at'])
        logger.exception('job_id=%s failed: %s', job_id, exc)

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
