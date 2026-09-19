"""Orchestration for AI question generation and exam assembly."""
import logging

from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from document.models import Document
from exam.llm import get_llm_provider
from exam.models import (
    ExamQuestion,
    Label,
    Option,
    Question,
    QuestionGenerationJob,
    QuestionType,
)
from exam.utils.llm_json import parse_questions
from exam.utils.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class ExamService:
    """Assemble and maintain exam question placements."""

    @transaction.atomic
    def add_questions(self, exam, question_ids):
        ordered_ids = list(dict.fromkeys(question_ids))
        questions = {
            q.id: q
            for q in Question.objects.filter(pk__in=ordered_ids)
        }
        missing = [qid for qid in ordered_ids if qid not in questions]
        if missing:
            raise ValidationError(
                {'question_ids': f'invalid ids: {sorted(missing)}'},
            )

        mismatched = [
            qid
            for qid in ordered_ids
            if questions[qid].grade_id != exam.grade_id
            or questions[qid].subject_id != exam.subject_id
        ]
        if mismatched:
            raise ValidationError(
                {
                    'question_ids': (
                        'questions must match exam grade and subject: '
                        f'{sorted(mismatched)}'
                    ),
                },
            )

        existing = set(
            ExamQuestion.objects.filter(
                exam=exam,
                question_id__in=ordered_ids,
            ).values_list('question_id', flat=True),
        )
        next_order = (
            ExamQuestion.objects.filter(exam=exam).aggregate(m=Max('order'))['m']
            or 0
        )

        to_create = []
        for qid in ordered_ids:
            if qid in existing:
                continue
            question = questions[qid]
            next_order += 1
            to_create.append(
                ExamQuestion(
                    exam=exam,
                    question=question,
                    order=next_order,
                    marks=question.marks,
                ),
            )

        if to_create:
            ExamQuestion.objects.bulk_create(to_create)
            exam.refresh_totals()
            logger.info(
                'exam %s added %s questions count=%s marks=%s',
                exam.id,
                len(to_create),
                exam.question_count,
                exam.total_marks,
            )

        return exam

    @transaction.atomic
    def reorder_questions(self, exam, items):
        placements = {
            eq.id: eq
            for eq in ExamQuestion.objects.filter(exam=exam).select_for_update()
        }
        missing = [
            item['exam_question_id']
            for item in items
            if item['exam_question_id'] not in placements
        ]
        if missing:
            raise ValidationError(
                {'items': f'invalid exam_question_id: {sorted(missing)}'},
            )

        orders = [item['order'] for item in items]
        if len(orders) != len(set(orders)):
            raise ValidationError({'items': 'duplicate order values'})

        proposed = {eq_id: eq.order for eq_id, eq in placements.items()}
        for item in items:
            proposed[item['exam_question_id']] = item['order']
        if len(proposed) != len(set(proposed.values())):
            raise ValidationError(
                {'items': 'order values collide with existing placements'},
            )

        # Two-phase update avoids unique (exam, order) collisions mid-swap.
        offset = (max(proposed.values()) if proposed else 0) + len(items) + 1
        for index, item in enumerate(items):
            placement = placements[item['exam_question_id']]
            placement.order = offset + index
            placement.save(update_fields=['order'])

        for item in items:
            placement = placements[item['exam_question_id']]
            placement.order = item['order']
            placement.save(update_fields=['order'])

        logger.info('exam %s reordered %s questions', exam.id, len(items))
        return exam



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
            label_names = item.pop('labels', []) or []
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
            if label_names:
                question.labels.set(self._resolve_labels(label_names))
            if question.question_type == QuestionType.MCQ:
                Option.objects.bulk_create([
                    Option(
                        question=question,
                        text=opt['text'],
                        is_correct=opt['is_correct'],
                        order=index,
                    )
                    for index, opt in enumerate(options, start=1)
                ])

    @staticmethod
    def _resolve_labels(names: list[str]) -> list[Label]:
        labels = []
        for name in names:
            label = Label.objects.filter(name__iexact=name).first()
            if label is None:
                label = Label.objects.create(name=name)
            labels.append(label)
        return labels
