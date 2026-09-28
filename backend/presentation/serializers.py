from rest_framework import serializers

from presentation.constants import MAX_PROMPT_LENGTH
from presentation.models import Conversation, Message, Presentation


class PresentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presentation
        fields = (
            'id',
            'title',
            'google_presentation_id',
            'url',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class PresentationPromptSerializer(serializers.Serializer):
    """Omit ``presentation`` to create a new deck; set it to edit that deck."""

    prompt = serializers.CharField(max_length=MAX_PROMPT_LENGTH, trim_whitespace=True)
    presentation = serializers.PrimaryKeyRelatedField(
        queryset=Presentation.objects.none(),
        required=False,
        allow_null=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context['request'].user
        self.fields['presentation'].queryset = Presentation.objects.filter(
            created_by=user,
        )


class MessageSerializer(serializers.ModelSerializer):
    presentation = PresentationSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'role', 'content', 'presentation', 'is_error', 'created_at')
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ('id', 'title', 'created_at', 'updated_at')
        read_only_fields = fields


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    presentations = PresentationSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ('messages', 'presentations')
        read_only_fields = fields


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=MAX_PROMPT_LENGTH, trim_whitespace=True)
