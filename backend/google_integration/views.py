import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from google_integration.services.google_auth import (
    GoogleAuthError,
    google_auth_service,
)

logger = logging.getLogger(__name__)


class GoogleAuthHealthView(APIView):
    """Confirm a Google access token can be obtained.

    The response reports success or a safe error message. It never includes
    the access token or refresh token.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            google_auth_service.get_access_token()
        except GoogleAuthError as exc:
            logger.warning('Google auth health check failed: %s', exc)
            return Response(
                {'status': 'error', 'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({'status': 'ok'})
