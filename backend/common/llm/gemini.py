import logging

import requests
from django.conf import settings

from common.constants import EMBEDDING_DIMENSIONS, JSON, LLM_TIMEOUT, TEXT
from common.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_DEFAULT_EMBEDDING_MODEL = 'text-embedding-004'


class GeminiLLMProvider(LLMProvider):
    @property
    def embedding_model(self):
        return settings.EMBEDDING_MODEL or _DEFAULT_EMBEDDING_MODEL

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

    def embed(self, texts):
        if not texts:
            return []
        if not settings.LLM_API_KEY:
            raise ValueError('LLM_API_KEY required for gemini')

        model = self.embedding_model
        url = f'{settings.LLM_BASE_URL}{model}:batchEmbedContents'
        payload = {
            'requests': [
                {
                    'model': f'models/{model}',
                    'content': {'parts': [{'text': text}]},
                    'outputDimensionality': EMBEDDING_DIMENSIONS,
                }
                for text in texts
            ],
        }

        logger.info(
            'gemini embed model=%s count=%s dims=%s',
            model,
            len(texts),
            EMBEDDING_DIMENSIONS,
        )

        resp = requests.post(
            url,
            params={'key': settings.LLM_API_KEY},
            json=payload,
            timeout=LLM_TIMEOUT,
        )
        if not resp.ok:
            logger.error(
                'Gemini embed error status=%s body=%s',
                resp.status_code,
                resp.text,
            )
            resp.raise_for_status()

        try:
            embeddings = resp.json()['embeddings']
            vectors = [item['values'] for item in embeddings]
        except (KeyError, TypeError) as exc:
            raise ValueError('bad gemini embedding response') from exc

        if len(vectors) != len(texts):
            raise ValueError(
                f'gemini embed count mismatch: expected {len(texts)} got {len(vectors)}',
            )
        return vectors
