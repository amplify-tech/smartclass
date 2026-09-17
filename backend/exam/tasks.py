"""Background tasks for the exam app."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_questions(self, job_id: int):
    logger.info('generate_questions started job_id=%s', job_id)
    from exam.services import QuestionGenerationService

    QuestionGenerationService().run_generation(job_id)
    return {'job_id': job_id}
