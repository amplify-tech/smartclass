from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from presentation.chat import ChatService
from presentation.exceptions import PresentationCommandFailed
from presentation.models import Conversation, Presentation
from presentation.plan import CREATE
from presentation.serializers import (
    ConversationDetailSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    PresentationPromptSerializer,
    PresentationSerializer,
)
from presentation.services import PresentationService


class ConversationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Teacher's presentation chats. Every message goes through ``POST {id}/messages/``."""

    permission_classes = [IsAuthenticated]
    search_fields = ['title']

    def get_queryset(self):
        return Conversation.objects.filter(created_by=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        if self.action == 'messages':
            return MessageCreateSerializer
        return ConversationSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def messages(self, request, pk=None):
        """Send a teacher message; returns the whole updated conversation."""
        conversation = self.get_object()
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ChatService().send(conversation, serializer.validated_data['content'])
        conversation = self.get_queryset().prefetch_related(
            'messages__presentation', 'presentations',
        ).get(pk=conversation.pk)
        return Response(ConversationDetailSerializer(conversation).data)


class PresentationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Teacher's presentations. All edits go through ``POST prompt/``."""

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

    @action(detail=False, methods=['post'], serializer_class=PresentationPromptSerializer)
    def prompt(self, request):
        """Create or update a presentation from a natural-language instruction."""
        serializer = PresentationPromptSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data.get('presentation')

        try:
            record, result = PresentationService().run_prompt(
                request.user,
                serializer.validated_data['prompt'],
                selected,
            )
        except PresentationCommandFailed as exc:
            return Response(
                {
                    'detail': str(exc.detail),
                    'presentation': (
                        PresentationSerializer(exc.presentation).data
                        if exc.presentation else None
                    ),
                    'steps': exc.steps,
                },
                status=exc.status_code,
            )

        return Response(
            {
                'intent': result['intent'],
                'presentation': PresentationSerializer(record).data,
                'slides': result['slides'],
                'steps': result['steps'],
            },
            status=(
                status.HTTP_201_CREATED
                if result['intent'] == CREATE
                else status.HTTP_200_OK
            ),
        )
