import logging

import requests
from django.conf import settings

from common.constants import JSON, LLM_TIMEOUT, TEXT
from common.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiLLMProvider(LLMProvider):
    def generate(
        self,
        *,
        system_prompt,
        user_prompt,
        response_format=TEXT,
    ):
        if not settings.LLM_API_KEY:
            raise ValueError('LLM_API_KEY required for gemini')

        url = f'{settings.LLM_BASE_URL}{settings.LLM_MODEL}:generateContent'

        payload = {
            'system_instruction': {'parts': [{'text': system_prompt}]},
            'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        }
        if response_format == JSON:
            payload['generationConfig'] = {
                'responseMimeType': 'application/json',
            }

        logger.info('gemini llm model=%s format=%s', settings.LLM_MODEL, response_format)

        resp = requests.post(
            url,
            params={'key': settings.LLM_API_KEY},
            json=payload,
            timeout=LLM_TIMEOUT,
        )

        if not resp.ok:
            logger.error(
                'Gemini error status=%s body=%s',
                resp.status_code,
                resp.text,
            )
            resp.raise_for_status()
        try:
            content = resp.json()['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError('bad gemini response') from exc
        if not content:
            raise ValueError('empty response from gemini')
        return content
