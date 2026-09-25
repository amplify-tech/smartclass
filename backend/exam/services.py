"""Orchestration for AI question generation and exam assembly."""
import logging

from django.db import transaction
from django.db.models import Max
from rest_framework.exceptions import ValidationError

from common.constants import GENERATE_QUESTIONS, JSON
from common.exceptions import ConflictError, TaskFailed
from common.utils import dedupe_preserve_order
from document.models import Document, Grade, Subject
from common.llm.factory import get_llm_provider
from exam.models import (
    Exam,
    ExamQuestion,
    Option,
    Question,
    QuestionType,
)
from exam.utils.labels import resolve_labels
from exam.utils.llm_json import parse_questions
from exam.utils.prompts import SYSTEM_PROMPT, build_user_prompt
from task.models import Job
from task.services import create_and_submit_job

logger = logging.getLogger(__name__)

_GENERATION_ERROR_GENERIC = 'Question generation failed. Please try again.'
_GENERATION_ERROR_PARSE = (
    'Could not process the generated questions. Please try again.'
)
_GENERATION_ERROR_TIMEOUT = 'Question generation timed out. Please try again.'


class ExamService:
    """Assemble and maintain exam question placements."""

    @staticmethod
    def _lock_exam(exam):
        return Exam.objects.select_for_update().get(pk=exam.pk)

    @transaction.atomic
    def add_questions(self, exam, question_ids):
        exam = self._lock_exam(exam)

        ordered_ids = dedupe_preserve_order(question_ids)
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
        exam = self._lock_exam(exam)

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

        proposed = {eq_id: eq.order for eq_id, eq in placements.items()}
        for item in items:
            proposed[item['exam_question_id']] = item['order']
        if len(proposed) != len(set(proposed.values())):
            raise ConflictError(
                'order values collide with existing placements',
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

    @transaction.atomic
    def remove_placement(self, exam, placement):
        exam = self._lock_exam(exam)

        deleted, _ = ExamQuestion.objects.filter(
            pk=placement.pk,
            exam=exam,
        ).delete()
        if deleted:
            exam.refresh_totals()
        return exam


class QuestionGenerationService:
    def create_job(self, user, data):
        """Validate docs, persist a task.Job, enqueue background generation."""
        document_ids = list(data.get('document_ids') or [])
        self._get_documents(user, document_ids)

        grade = data['grade']
        subject = data['subject']
        payload = {
            'grade': grade.pk,
            'subject': subject.pk,
            'difficulty': data['difficulty'],
            'total_marks': data['total_marks'],
            'question_types': data['question_types'],
            'description': data.get('description') or '',
            'document_ids': document_ids,
        }

        job = create_and_submit_job(
            task_type=GENERATE_QUESTIONS,
            payload=payload,
            request_user_id=user.id,
        )
        logger.info('generation job created id=%s', job.id)
        return job

    def _get_documents(self, user, document_ids):
        if not document_ids:
            return []

        ids = set(document_ids)
        docs = list(
            Document.objects.filter(
                uploaded_by=user,
                pk__in=ids,
                status=Document.Status.READY,
            )
        )
        missing = ids - {d.pk for d in docs}
        if missing:
            raise ValidationError(
                {'document_ids': f'invalid or not-ready ids: {sorted(missing)}'},
            )
        return docs

    def run_generation(self, job_id, payload):
        """LLM work for an existing task.Job. Status is owned by task_runner."""
        try:
            job = Job.objects.select_related('created_by').get(pk=job_id)
        except Job.DoesNotExist:
            logger.warning('job not found id=%s', job_id)
            raise TaskFailed(_GENERATION_ERROR_GENERIC)

        try:
            grade = Grade.objects.get(pk=payload['grade'])
            subject = Subject.objects.get(pk=payload['subject'])
        except (Grade.DoesNotExist, Subject.DoesNotExist, KeyError) as exc:
            logger.exception('invalid generation payload job_id=%s', job_id)
            raise TaskFailed(_GENERATION_ERROR_GENERIC) from exc

        try:
            prompt = build_user_prompt(
                grade_name=grade.name,
                subject_name=subject.name,
                difficulty=payload.get('difficulty'),
                total_marks=payload.get('total_marks'),
                question_types=payload.get('question_types') or {},
                description=payload.get('description') or '',
            )
            raw = get_llm_provider().generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                response_format=JSON,
            )
            questions = parse_questions(raw)
            question_ids = self._save_questions(
                job=job,
                grade=grade,
                subject=subject,
                difficulty=payload.get('difficulty'),
                items=questions,
            )
            logger.info('job done id=%s count=%s', job_id, len(question_ids))
            return {'question_ids': question_ids}
        except TaskFailed:
            raise
        except Exception as exc:
            logger.exception('job failed id=%s', job_id)
            raise TaskFailed(self._safe_error_message(exc)) from exc

    @staticmethod
    def _safe_error_message(exc):
        """Return a client-safe message; never expose raw exception text."""
        if isinstance(exc, (ValueError, TypeError, KeyError)):
            return _GENERATION_ERROR_PARSE
        name = type(exc).__name__.lower()
        message = str(exc).lower()
        if 'timeout' in name or 'timeout' in message or 'timed out' in message:
            return _GENERATION_ERROR_TIMEOUT
        return _GENERATION_ERROR_GENERIC

    @transaction.atomic
    def _save_questions(self, *, job, grade, subject, difficulty, items):
        Question.objects.filter(generation_job=job).delete()

        question_ids = []
        for item in items:
            options = item.get('options') or []
            label_names = item.get('labels') or []
            question = Question.objects.create(
                question_type=item['question_type'],
                text=item['text'],
                difficulty=item.get('difficulty') or difficulty,
                marks=item['marks'],
                grade=grade,
                subject=subject,
                correct_answer=item.get('correct_answer', ''),
                generation_job=job,
                created_by=job.created_by,
            )
            question_ids.append(question.id)
            if label_names:
                question.labels.set(resolve_labels(label_names))
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
        return question_ids
