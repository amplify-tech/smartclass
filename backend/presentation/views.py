from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from presentation.models import Presentation
from presentation.serializers import PresentationSerializer
from presentation.services import PresentationService


class PresentationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """A teacher's saved presentations. Chat creates and edits them."""

    serializer_class = PresentationSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['title']

    def get_queryset(self):
        return Presentation.objects.filter(created_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        presentation = self.get_object()
        slides = PresentationService().get_slides(presentation)
        return Response({
            **PresentationSerializer(presentation).data,
            'slides': slides,
        })

    def perform_destroy(self, instance):
        PresentationService().delete(instance)
