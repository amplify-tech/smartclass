from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from exam.models import (
    Difficulty,
    Exam,
    ExamQuestion,
    Label,
    Question,
    QuestionGenerationJob,
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
    UpdateExamQuestionSerializer,
)
from exam.services import ExamService, QuestionGenerationService


class QuestionGenerationJobViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Jobs are scoped to the authenticated owner only (list + retrieve)."""

    serializer_class = QuestionGenerationJobSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    pagination_class = None

    def get_queryset(self):
        return QuestionGenerationJob.objects.filter(
            created_by=self.request.user,
        ).select_related('grade', 'subject')

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


class LabelViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
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
            qs = qs.filter(text__icontains=search)

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

        grade = params.get('grade')
        if grade is not None and grade != '':
            qs = qs.filter(grade_id=grade)

        subject = params.get('subject')
        if subject is not None and subject != '':
            qs = qs.filter(subject_id=subject)

        generation_job = params.get('generation_job') or params.get('job_id')
        if generation_job is not None and generation_job != '':
            # Only the job owner can filter questions by that job.
            qs = qs.filter(
                generation_job_id=generation_job,
                generation_job__created_by=self.request.user,
            )

        label_ids = params.getlist('label')
        if label_ids:
            qs = qs.filter(labels__in=label_ids).distinct()

        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ExamViewSet(viewsets.ModelViewSet):
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
        methods=['patch', 'delete'],
        url_path=r'exam-questions/(?P<exam_question_id>[0-9]+)',
    )
    def exam_question_detail(self, request, pk=None, exam_question_id=None):
        exam = self.get_object()
        placement = get_object_or_404(ExamQuestion, pk=exam_question_id, exam=exam)

        if request.method == 'DELETE':
            placement.delete()
            exam.refresh_totals()
            return Response(self._serialized_exam(exam))

        serializer = UpdateExamQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(placement, key, value)
        placement.save()
        if 'marks' in serializer.validated_data:
            exam.refresh_totals()
        return Response(self._serialized_exam(exam))
