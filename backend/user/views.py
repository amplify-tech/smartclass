import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from user.serializers import (
    LoginTokenObtainPairSerializer,
    ProfileSerializer,
    RegisterSerializer,
)

logger = logging.getLogger(__name__)


class LoginView(TokenObtainPairView):
    """Issue JWTs. Missing account and wrong password are field errors."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginTokenObtainPairSerializer


class ProfileView(APIView):
    """Return the current authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: ProfileSerializer})
    def get(self, request, *args, **kwargs):
        return Response(ProfileSerializer(request.user).data)


class RegisterView(APIView):
    """Create a new user account."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=RegisterSerializer, responses={201: RegisterSerializer})
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info('user registered user_id=%s', user.id)
        return Response(RegisterSerializer(user).data, status=status.HTTP_201_CREATED)
