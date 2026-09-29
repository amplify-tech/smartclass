from rest_framework import serializers

from chat.models import Conversation, Message
from common.constants import CHAT_MESSAGES_LIMIT, MAX_MESSAGE_LENGTH


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ('id', 'chat_type', 'title', 'created_at', 'updated_at')
        read_only_fields = ('id', 'title', 'created_at', 'updated_at')


class ConversationCreateSerializer(serializers.ModelSerializer):
    context = serializers.JSONField(default=dict)

    class Meta:
        model = Conversation
        fields = ('id', 'chat_type', 'context', 'title', 'created_at', 'updated_at')
        read_only_fields = ('id', 'title', 'created_at', 'updated_at')

    def validate_context(self, value):
        if value is None or not isinstance(value, dict):
            raise serializers.ValidationError('Context must be an object.')
        return value


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('id', 'role', 'content', 'is_error', 'created_at')
        read_only_fields = fields


class ConversationDetailSerializer(ConversationSerializer):
    messages = serializers.SerializerMethodField()

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ('context', 'messages')
        read_only_fields = fields

    def get_messages(self, conversation):
        recent = list(
            conversation.messages.order_by('-created_at', '-id')[:CHAT_MESSAGES_LIMIT]
        )
        recent.reverse()
        return MessageSerializer(recent, many=True).data


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=MAX_MESSAGE_LENGTH, trim_whitespace=True)
