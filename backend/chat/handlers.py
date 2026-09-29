from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatReply:
    content: str
    # Always a dict. ``{}`` clears stored state.
    context: dict
    is_error: bool = False


class ChatHandler(ABC):
    """Answers one chat type. The caller passes this strategy into ``ChatService``."""

    @abstractmethod
    def respond(self, conversation, content: str, history: list[tuple[str, str]]) -> ChatReply:
        """Reply to ``content``.

        ``history`` is the previous ``(role, content)`` pairs the service loaded,
        oldest first. ``conversation.context`` is this handler's state.
        ``ChatReply.context`` must be a dict.
        """
