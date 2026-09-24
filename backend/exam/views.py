from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.constants import GENERATE_QUESTIONS
from common.exceptions import ConflictError
from common.utils import parse_positive_int
from exam.models import (
    Difficulty,
    Exam,
    ExamQuestion,
    Label,
    Question,
    QuestionType,
)
from exam.permissions import IsOwnerOrReadOnly
from exam.serializers import (
    AddExamQuestionsSerializer,
    ExamListSerializer,
    ExamSerializer,
    LabelSerializer,
    QuestionGenerationJobSerializer,
    QuestionSerializer,
    ReorderExamQuestionsSerializer,
)
from exam.services import ExamService, QuestionGenerationService
from task.models import Job


class QuestionGenerationJobViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Façade over task.Job for GENERATE_QUESTIONS (owner-scoped)."""

    serializer_class = QuestionGenerationJobSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    pagination_class = None

    def get_queryset(self):
        return Job.objects.filter(
            created_by=self.request.user,
            task_type=GENERATE_QUESTIONS,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = QuestionGenerationService().create_job(
            request.user,
            serializer.validated_data.copy(),
        )
        return Response(
            self.get_serializer(job).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'], url_path='latest')
    def latest(self, request):
        """Return only the current user's most recent generation job id."""
        job_id = (
            self.get_queryset()
            .order_by('-id')
            .values_list('id', flat=True)
            .first()
        )
        if job_id is None:
            return Response(
                {'detail': 'No generation jobs found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'id': job_id})


class LabelViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    pagination_class = None


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = (
            Question.objects.all()
            .select_related(
                'grade',
                'subject',
                'source_document',
                'generation_job',
            )
            .prefetch_related('options', 'labels')
        )

        params = self.request.query_params

        search = (params.get('search') or '').strip()
        if search:
            qs = qs.filter(text__icontains=search[:200])

        question_type = (params.get('question_type') or '').strip().lower()
        if question_type:
            valid_types = {choice.value for choice in QuestionType}
            if question_type in valid_types:
                qs = qs.filter(question_type=question_type)

        difficulty = (params.get('difficulty') or '').strip().lower()
        if difficulty:
            valid_difficulties = {choice.value for choice in Difficulty}
            if difficulty in valid_difficulties:
                qs = qs.filter(difficulty=difficulty)

        grade_id = parse_positive_int(params.get('grade'))
        if grade_id is not None:
            qs = qs.filter(grade_id=grade_id)

        subject_id = parse_positive_int(params.get('subject'))
        if subject_id is not None:
            qs = qs.filter(subject_id=subject_id)

        generation_job = params.get('generation_job') or params.get('job_id')
        job_id = parse_positive_int(generation_job)
        if job_id is not None:
            # Only the job owner can filter questions by that job.
            qs = qs.filter(
                generation_job_id=job_id,
                generation_job__created_by=self.request.user,
            )

        label_ids = [
            lid
            for lid in (parse_positive_int(v) for v in params.getlist('label'))
            if lid is not None
        ]
        if label_ids:
            qs = qs.filter(labels__in=label_ids).distinct()

        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ConflictError(
                'Cannot delete a question that is used on an exam. '
                'Remove it from exams first.',
            )


class ExamViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    # put required for reorder-questions action
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExamListSerializer
        return ExamSerializer

    def get_queryset(self):
        qs = Exam.objects.filter(created_by=self.request.user).select_related(
            'grade',
            'subject',
        )
        if self.action in (
            'retrieve',
            'add_questions',
            'reorder_questions',
            'exam_question_detail',
        ):
            qs = qs.prefetch_related(
                'exam_questions__question__options',
                'exam_questions__question__labels',
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _serialized_exam(self, exam):
        exam = self.get_queryset().get(pk=exam.pk)
        return ExamSerializer(exam).data

    @action(detail=True, methods=['post'], url_path='questions')
    def add_questions(self, request, pk=None):
        exam = self.get_object()
        serializer = AddExamQuestionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ExamService().add_questions(exam, serializer.validated_data['question_ids'])
        return Response(self._serialized_exam(exam))

    @action(detail=True, methods=['put'], url_path='reorder-questions')
    def reorder_questions(self, request, pk=None):
        exam = self.get_object()
        serializer = ReorderExamQuestionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ExamService().reorder_questions(exam, serializer.validated_data['items'])
        return Response(self._serialized_exam(exam))

    @action(
        detail=True,
        methods=['delete'],
        url_path=r'exam-questions/(?P<exam_question_id>[0-9]+)',
    )
    def exam_question_detail(self, request, pk=None, exam_question_id=None):
        exam = self.get_object()
        placement = get_object_or_404(ExamQuestion, pk=exam_question_id, exam=exam)
        ExamService().remove_placement(exam, placement)
        return Response(self._serialized_exam(exam))
