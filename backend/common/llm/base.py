from abc import ABC, abstractmethod
from typing import Literal

from common.constants import JSON, TEXT

ResponseFormat = Literal[TEXT, JSON]


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_format: ResponseFormat = TEXT,
    ) -> str:
        pass

    @property
    @abstractmethod
    def embedding_model(self) -> str:
        """Configured embedding model id for this provider."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per text, in the same order."""
