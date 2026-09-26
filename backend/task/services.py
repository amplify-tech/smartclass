"""Public API for submitting jobs onto the shared executor."""

import logging

from concurrent.futures import ThreadPoolExecutor

from common.constants import MAX_RETRIES
from common.exceptions import ConflictError

from .models import Job
from .task_runner import run_job

logger = logging.getLogger(__name__)


"""Single process-wide thread pool for background jobs"""
_executor = ThreadPoolExecutor(max_workers=2)


def submit_job(job_id, request_user_id=None):
    """Enqueue job.id on the shared pool"""
    logger.info(
        'submit_job job_id=%s request_user_id=%s',
        job_id,
        request_user_id,
    )
    _executor.submit(run_job, job_id, request_user_id)


def create_and_submit_job(*, task_type, payload=None, request_user_id=None):
    """Create a Job owned by request_user_id and enqueue it"""
    job = Job.objects.create(
        task_type=task_type,
        payload=payload or {},
        created_by_id=request_user_id,
    )
    submit_job(job.id, request_user_id=request_user_id)
    return job


def retry_job(job, request_user_id=None):
    """Reset a job and re-enqueue it via submit_job."""
    if job.status == Job.Status.RUNNING:
        raise ConflictError('Job is currently running.')
    if job.retry_count >= MAX_RETRIES:
        raise ConflictError('Job has reached the maximum number of retries.')

    job.status = Job.Status.PENDING
    job.retry_count += 1
    job.error = ''
    job.result = None
    job.started_at = None
    job.completed_at = None
    job.save(
        update_fields=[
            'status',
            'retry_count',
            'error',
            'result',
            'started_at',
            'completed_at',
        ]
    )
    submit_job(job.id, request_user_id=request_user_id)
    logger.info(
        'retry_job job_id=%s retry_count=%s request_user_id=%s',
        job.id,
        job.retry_count,
        request_user_id,
    )
    return job
