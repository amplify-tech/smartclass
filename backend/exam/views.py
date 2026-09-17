from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from exam.models import Exam, ExamQuestion, Question, QuestionGenerationJob
from exam.serializers import (
    AddExamQuestionsSerializer,
    ExamListSerializer,
    ExamSerializer,
    QuestionGenerationJobSerializer,
    QuestionSerializer,
    ReorderExamQuestionsSerializer,
    UpdateExamQuestionSerializer,
)
from exam.services import QuestionGenerationService


class QuestionGenerationJobViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = QuestionGenerationJobSerializer
    http_method_names = ['get', 'post', 'head', 'options']

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


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return (
            Question.objects.filter(created_by=self.request.user)
            .select_related('grade', 'subject', 'source_document', 'generation_job')
            .prefetch_related('options')
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ExamViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExamListSerializer
        return ExamSerializer

    def get_queryset(self):
        qs = Exam.objects.filter(created_by=self.request.user).select_related(
            'grade',
            'subject',
        )
        if self.action == 'retrieve':
            qs = qs.prefetch_related('exam_questions__question__options')
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='questions')
    def add_questions(self, request, pk=None):
        exam = self.get_object()
        serializer = AddExamQuestionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: create ExamQuestion rows for validated question_ids
        return Response(ExamSerializer(exam).data)

    @action(detail=True, methods=['put'], url_path='reorder-questions')
    def reorder_questions(self, request, pk=None):
        exam = self.get_object()
        serializer = ReorderExamQuestionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: update order for each item
        return Response(ExamSerializer(exam).data)

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
            return Response(ExamSerializer(exam).data)

        serializer = UpdateExamQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(placement, key, value)
        placement.save()
        return Response(ExamSerializer(exam).data)
