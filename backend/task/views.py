from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Job
from .serializers import JobStatusSerializer
from .services import retry_job


class JobViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Owner-only job status for React polling."""

    serializer_class = JobStatusSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    pagination_class = None

    def get_queryset(self):
        return Job.objects.filter(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        job = retry_job(self.get_object(), request_user_id=request.user.id)
        return Response(self.get_serializer(job).data)
