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
from chat.services import ChatService


class ConversationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """User's AI chats. Every message goes through ``POST {id}/messages/``."""

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
        """Send a user message; returns the whole updated conversation."""
        conversation = self.get_object()
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ChatService().send(conversation, serializer.validated_data['content'])
        conversation = self.get_queryset().prefetch_related('messages').get(pk=conversation.pk)
        return Response(ConversationDetailSerializer(conversation).data)
