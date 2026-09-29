from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase

from chat.handlers import ChatHandler, ChatReply
from chat.models import Conversation, Message
from chat.serializers import ConversationCreateSerializer, ConversationDetailSerializer
from chat.services import ChatService, handler_for
from common.constants import CHAT_MESSAGES_LIMIT
from user.models import User


class _RecordingHandler(ChatHandler):
    def __init__(self, context):
        self.context = context
        self.history = None

    def respond(self, conversation, content, history):
        self.history = history
        return ChatReply(content=f'echo {content}', context=self.context)


class HandlerLookupTests(SimpleTestCase):
    def test_presentation_chat_type_uses_the_presentation_handler(self):
        from presentation.chat import PresentationChatHandler

        self.assertIsInstance(handler_for('presentation'), PresentationChatHandler)

    def test_unknown_chat_type_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            handler_for('exam')


class ChatServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='teacher@example.com', password='secret')
        self.conversation = Conversation.objects.create(
            chat_type=Conversation.ChatType.PRESENTATION,
            created_by=self.user,
            context={},
        )

    def test_send_passes_only_the_previous_message(self):
        Message.objects.create(conversation=self.conversation, role=Message.Role.USER, content='first')
        Message.objects.create(
            conversation=self.conversation, role=Message.Role.ASSISTANT, content='second',
        )
        handler = _RecordingHandler({'presentations': []})
        ChatService(handler).send(self.conversation, 'third')
        self.assertEqual(handler.history, [(Message.Role.ASSISTANT, 'second')])
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.context, {'presentations': []})

    def test_send_rejects_none_context(self):
        handler = _RecordingHandler(None)
        with self.assertRaises(TypeError):
            ChatService(handler).send(self.conversation, 'hello')


class ConversationSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='teacher2@example.com', password='secret')

    def test_empty_context_is_valid(self):
        serializer = ConversationCreateSerializer(data={
            'chat_type': Conversation.ChatType.PRESENTATION,
            'context': {},
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_null_context_is_rejected(self):
        serializer = ConversationCreateSerializer(data={
            'chat_type': Conversation.ChatType.PRESENTATION,
            'context': None,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('context', serializer.errors)

    def test_detail_returns_only_the_newest_messages(self):
        conversation = Conversation.objects.create(
            chat_type=Conversation.ChatType.PRESENTATION,
            created_by=self.user,
            context={},
        )
        for number in range(CHAT_MESSAGES_LIMIT + 5):
            Message.objects.create(
                conversation=conversation,
                role=Message.Role.USER,
                content=f'message {number}',
            )
        messages = ConversationDetailSerializer(conversation).data['messages']
        self.assertEqual(len(messages), CHAT_MESSAGES_LIMIT)
        self.assertEqual(messages[0]['content'], 'message 5')
        self.assertEqual(messages[-1]['content'], f'message {CHAT_MESSAGES_LIMIT + 4}')
