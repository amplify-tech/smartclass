"""Orchestration for AI question generation."""
import logging

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from document.models import Document
from exam.llm import get_llm_provider
from exam.models import Option, Question, QuestionGenerationJob, QuestionType
from exam.utils.llm_json import parse_questions
from exam.utils.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    def create_job(self, user, data: dict):
        document_ids = data.pop('document_ids', []) or []
        documents = self._get_documents(user, document_ids)

        job = QuestionGenerationJob.objects.create(created_by=user, **data)
        if documents:
            job.documents.set(documents)

        logger.info('job created id=%s', job.id)
        from exam.tasks import generate_questions

        generate_questions.delay(job.id)
        return job

    def _get_documents(self, user, document_ids):
        if not document_ids:
            return []

        ids = list(set(document_ids))
        docs = list(
            Document.objects.filter(
                uploaded_by=user,
                pk__in=ids,
                status=Document.Status.READY,
            )
        )
        missing = set(ids) - {d.pk for d in docs}
        if missing:
            raise ValidationError(
                {'document_ids': f'invalid or not-ready ids: {sorted(missing)}'},
            )
        return docs

    def run_generation(self, job_id: int):
        try:
            job = QuestionGenerationJob.objects.select_related(
                'grade', 'subject', 'created_by',
            ).get(pk=job_id)
        except QuestionGenerationJob.DoesNotExist:
            logger.warning('job not found id=%s', job_id)
            return

        job.status = QuestionGenerationJob.Status.RUNNING
        job.save(update_fields=['status'])

        try:
            raw = get_llm_provider().generate(SYSTEM_PROMPT, build_user_prompt(job))
            questions = parse_questions(raw)
            self._save_questions(job, questions)

            job.status = QuestionGenerationJob.Status.COMPLETED
            job.completed_at = timezone.now()
            job.error_message = ''
            job.save(update_fields=['status', 'completed_at', 'error_message'])
            logger.info('job done id=%s count=%s', job_id, len(questions))
        except Exception as exc:
            logger.exception('job failed id=%s', job_id)
            job.status = QuestionGenerationJob.Status.FAILED
            job.error_message = str(exc)[:2000]
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_message', 'completed_at'])
            raise

    @transaction.atomic
    def _save_questions(self, job, items):
        job.questions.all().delete()

        for item in items:
            options = item.pop('options', [])
            question = Question.objects.create(
                question_type=item['question_type'],
                text=item['text'],
                difficulty=item.get('difficulty') or job.difficulty,
                marks=item['marks'],
                grade=job.grade,
                subject=job.subject,
                correct_answer=item.get('correct_answer', ''),
                generation_job=job,
                created_by=job.created_by,
            )
            if question.question_type == QuestionType.MCQ:
                Option.objects.bulk_create([
                    Option(
                        question=question,
                        text=opt['text'],
                        is_correct=opt['is_correct'],
                        order=opt['order'],
                    )
                    for opt in options
                ])
