import logging

logger = logging.getLogger(__name__)


def generate_questions(*, job_id, **payload):
    """Background handler for GENERATE_QUESTIONS (kwargs = Job.payload)."""
    logger.info('generate_questions job_id=%s', job_id)
    from exam.services import QuestionGenerationService

    return QuestionGenerationService().run_generation(job_id, payload)
