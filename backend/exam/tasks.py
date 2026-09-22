import logging

logger = logging.getLogger(__name__)


def generate_questions(job_id: int):
    logger.info('generate_questions job_id=%s', job_id)
    from exam.services import QuestionGenerationService

    QuestionGenerationService().run_generation(job_id)
