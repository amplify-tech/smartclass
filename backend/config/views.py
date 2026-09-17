from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()


class HealthCheckView(APIView):
    """Simple liveness check for load balancers and local smoke tests."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: HealthCheckSerializer})
    def get(self, request, *args, **kwargs):
        return Response({'status': 'ok'})
