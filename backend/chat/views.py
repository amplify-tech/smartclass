from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chat.models import Conversation
from chat.serializers import (
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
)
from chat.services import ChatService, handler_for


class ConversationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Shared chat API. ``chat_type`` and ``context`` pick the behavior."""

    permission_classes = [IsAuthenticated]
    filterset_fields = ['chat_type']
    search_fields = ['title']

    def get_queryset(self):
        return Conversation.objects.filter(created_by=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        if self.action == 'messages':
            return MessageCreateSerializer
        return ConversationSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def messages(self, request, pk=None):
        """Send a user message; returns the updated conversation."""
        conversation = self.get_object()
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ChatService(handler_for(conversation.chat_type)).send(
            conversation, serializer.validated_data['content'],
        )
        conversation = self.get_queryset().get(pk=conversation.pk)
        return Response(ConversationDetailSerializer(conversation).data)
