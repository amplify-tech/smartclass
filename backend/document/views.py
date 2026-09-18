from rest_framework import mixins, viewsets

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


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Document.objects.filter(uploaded_by=self.request.user).select_related(
            'grade',
            'subject',
        )
        # TODO: filter by grade / subject / doc_type / status query params
        return qs
