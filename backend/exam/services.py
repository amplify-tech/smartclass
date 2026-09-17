"""Orchestration for AI question generation (Celery). Plain CRUD stays in views."""
import logging

from document.models import Document
from exam.models import QuestionGenerationJob

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    def create_job(self, user, data: dict):
        document_ids = data.pop('document_ids', []) or []
        documents = Document.objects.filter(
            uploaded_by=user,
            pk__in=document_ids,
            status=Document.Status.READY,
        )

        job = QuestionGenerationJob.objects.create(created_by=user, **data)
        if document_ids:
            job.documents.set(documents)

        logger.info('generation job created job_id=%s', job.id)

        from exam.tasks import generate_questions

        generate_questions.delay(job.id)
        return job

    def run_generation(self, job_id: int):
        """Called from Celery worker — RAG/LLM pipeline lives here."""
        # TODO: load job → RAG or LLM → save Questions → status
        logger.info('run_generation stub job_id=%s', job_id)
