from rest_framework import viewsets

from document.models import Document, Grade, Subject
from document.serializers import (
    DocumentSerializer,
    GradeSerializer,
    SubjectSerializer,
)


class GradeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    pagination_class = None


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    pagination_class = None


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """Teacher documents for exam material selection."""

    serializer_class = DocumentSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Document.objects.filter(uploaded_by=self.request.user).select_related(
            'grade',
            'subject',
        )
        # TODO: filter by grade / subject / doc_type / status query params
        return qs
