from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Job
from .serializers import JobStatusSerializer


class JobViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Owner-only job status for React polling."""

    serializer_class = JobStatusSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']
    pagination_class = None

    def get_queryset(self):
        return Job.objects.filter(created_by=self.request.user)
