from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from common.constants import PROCESS_DOCUMENT
from document.models import Document, Grade, Subject
from document.serializers import (
    DocumentSerializer,
    GradeSerializer,
    SubjectSerializer,
)
from task.services import create_and_submit_job


class GradeViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    http_method_names = ['get', 'post', 'head', 'options']
    pagination_class = None

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUser()]
        return [IsAuthenticated()]


class SubjectViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    http_method_names = ['get', 'post', 'head', 'options']
    pagination_class = None

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUser()]
        return [IsAuthenticated()]


class DocumentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    pagination_class = None
    filterset_fields = ['grade', 'subject', 'doc_type', 'status']
    search_fields = ['title']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return Document.objects.filter(
            uploaded_by=self.request.user,
        ).select_related(
            'grade',
            'subject',
        )

    def perform_create(self, serializer):
        document = serializer.save(uploaded_by=self.request.user)
        create_and_submit_job(
            task_type=PROCESS_DOCUMENT,
            payload={'document_id': document.pk},
            request_user_id=self.request.user.id,
        )

    def perform_destroy(self, instance):
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()
