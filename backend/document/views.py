from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from document.models import Document, Grade, Subject
from document.serializers import (
    DocumentSerializer,
    GradeSerializer,
    SubjectSerializer,
)


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


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Document.objects.filter(
            uploaded_by=self.request.user,
        ).select_related(
            'grade',
            'subject',
        )
