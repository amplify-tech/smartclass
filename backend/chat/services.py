"""Generic chat: store messages and context, and hand each new message to the chat type's handler."""

from chat.models import Conversation, Message
from presentation.chat import PresentationChatHandler

HANDLERS = {
    Conversation.ChatType.PRESENTATION: PresentationChatHandler,
}


def get_chat_handler(chat_type):
    return HANDLERS[chat_type]()


class ChatService:
    def send(self, conversation, content):
        """Save the user message, let the handler answer, then save its context and reply."""
        history = list(conversation.messages.values_list('role', 'content'))
        Message.objects.create(conversation=conversation, role=Message.Role.USER, content=content)

        reply = get_chat_handler(conversation.chat_type).respond(conversation, content, history)

        if reply.context is not None:
            conversation.context = reply.context
        if not conversation.title:
            conversation.title = content[:80]
        conversation.save(update_fields=['title', 'context', 'updated_at'])
        return Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=reply.content,
            is_error=reply.is_error,
        )
