from django.conf import settings

from common.llm.gemini import GeminiLLMProvider
from common.llm.local import LocalLLMProvider


def get_llm_provider():
    name = (settings.LLM_PROVIDER or 'local').lower()
    if name == 'local':
        return LocalLLMProvider()
    if name == 'gemini':
        return GeminiLLMProvider()
    raise ValueError(f'unknown LLM_PROVIDER={name}')
