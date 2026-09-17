import logging

import requests
from django.conf import settings

from exam.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiLLMProvider(LLMProvider):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not settings.LLM_API_KEY:
            raise ValueError('LLM_API_KEY required for gemini')

        url = (
            'https://generativelanguage.googleapis.com/v1beta/models/'
            f'{settings.LLM_MODEL}:generateContent'
        )
        payload = {
            'system_instruction': {'parts': [{'text': system_prompt}]},
            'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
            'generationConfig': {'responseMimeType': 'application/json'},
        }
        logger.info('gemini llm model=%s', settings.LLM_MODEL)
        resp = requests.post(
            url,
            params={'key': settings.LLM_API_KEY},
            json=payload,
            timeout=settings.LLM_TIMEOUT,
        )
        resp.raise_for_status()
        try:
            content = resp.json()['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError('bad gemini response') from exc
        if not content:
            raise ValueError('empty response from gemini')
        return content
