import logging

import requests
from django.conf import settings

from exam.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class LocalLLMProvider(LLMProvider):
    """Ollama /api/chat."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f'{settings.LLM_BASE_URL.rstrip("/")}/api/chat'
        payload = {
            'model': settings.LLM_MODEL,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'stream': False,
            'format': 'json',
        }
        logger.info('local llm model=%s', settings.LLM_MODEL)
        resp = requests.post(url, json=payload, timeout=settings.LLM_TIMEOUT)
        resp.raise_for_status()
        content = (resp.json().get('message') or {}).get('content', '')
        if not content:
            raise ValueError('empty response from local llm')
        return content
