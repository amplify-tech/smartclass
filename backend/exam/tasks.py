import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_questions(self, job_id: int):
    logger.info('generate_questions job_id=%s', job_id)
    from exam.services import QuestionGenerationService

    try:
        QuestionGenerationService().run_generation(job_id)
    except Exception as exc:
        raise self.retry(exc=exc)
