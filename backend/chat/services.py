"""Stores chat messages. ``chat_type`` selects the handler; the handler owns ``context``."""

import importlib

from django.core.exceptions import ImproperlyConfigured

from chat.handlers import ChatHandler
from chat.models import Conversation, Message
from common.constants import CHAT_HISTORY_LIMIT

# Loaded when a message is sent. The chat app does not import these classes itself.
_HANDLERS = {
    Conversation.ChatType.PRESENTATION: 'presentation.chat.PresentationChatHandler',
}


def handler_for(chat_type) -> ChatHandler:
    path = _HANDLERS.get(chat_type)
    if not path:
        raise ImproperlyConfigured(f'No chat handler for {chat_type!r}.')
    module_name, class_name = path.rsplit('.', 1)
    return getattr(importlib.import_module(module_name), class_name)()


class ChatService:
    def __init__(self, handler: ChatHandler):
        self.handler = handler

    def send(self, conversation, content):
        """Save the user message, let the handler answer, then save its context and reply."""
        if not isinstance(conversation.context, dict):
            raise TypeError('Chat context must be a dict.')
        history = list(
            conversation.messages.order_by('-created_at', '-id')
            .values_list('role', 'content')[:CHAT_HISTORY_LIMIT]
        )
        history.reverse()
        Message.objects.create(conversation=conversation, role=Message.Role.USER, content=content)

        reply = self.handler.respond(conversation, content, history)
        if not isinstance(reply.context, dict):
            raise TypeError('Chat context must be a dict.')

        if not conversation.title:
            conversation.title = content[:80]
        conversation.context = reply.context
        conversation.save(update_fields=['title', 'context', 'updated_at'])
        return Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=reply.content,
            is_error=reply.is_error,
        )
