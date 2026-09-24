"""Public API for submitting jobs onto the shared executor."""

import logging

from concurrent.futures import ThreadPoolExecutor
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
