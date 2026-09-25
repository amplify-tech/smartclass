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
