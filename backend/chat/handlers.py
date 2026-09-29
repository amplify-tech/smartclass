from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatReply:
    content: str
    is_error: bool = False
    # The conversation's new context; ``None`` keeps the current one.
    context: dict | None = None


class ChatHandler(ABC):
    """Answers one chat type. ``ChatService`` stores messages and context; handlers only reply."""

    @abstractmethod
    def respond(self, conversation, content: str, history: list[tuple[str, str]]) -> ChatReply:
        """Reply to ``content``.

        ``history`` is every earlier ``(role, content)``, oldest first.
        ``conversation.context`` is this handler's state; return the updated
        state in ``ChatReply.context``.
        """
