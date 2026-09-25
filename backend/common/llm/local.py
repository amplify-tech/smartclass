import logging

import requests
from django.conf import settings

from common.constants import JSON, LLM_TIMEOUT, RAG_EMBEDDING_MODEL, TEXT
from common.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class LocalLLMProvider(LLMProvider):
    """Ollama /api/chat and /api/embed."""

    @property
    def embedding_model(self):
        return settings.EMBEDDING_MODEL or RAG_EMBEDDING_MODEL

    def generate(
        self,
        *,
        system_prompt,
        user_prompt,
        response_format=TEXT,
    ):
        url = f'{settings.LLM_BASE_URL.rstrip("/")}/api/chat'
        payload = {
            'model': settings.LLM_MODEL,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'stream': False,
            'think': False,
        }
        if response_format == JSON:
            payload['format'] = JSON

        logger.info('local llm model=%s format=%s', settings.LLM_MODEL, response_format)
        resp = requests.post(url, json=payload, timeout=LLM_TIMEOUT)
        resp.raise_for_status()
        content = (resp.json().get('message') or {}).get('content', '')
        if not content:
            raise ValueError('empty response from local llm')
        return content

    def embed(self, texts):
        if not texts:
            return []

        model = self.embedding_model
        url = f'{settings.LLM_BASE_URL.rstrip("/")}/api/embed'
        payload = {
            'model': model,
            'input': texts,
        }

        logger.info('local embed model=%s count=%s', model, len(texts))
        resp = requests.post(url, json=payload, timeout=LLM_TIMEOUT)
        resp.raise_for_status()

        try:
            vectors = resp.json()['embeddings']
        except (KeyError, TypeError) as exc:
            raise ValueError('bad local embedding response') from exc

        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise ValueError(
                f'local embed count mismatch: expected {len(texts)} got '
                f'{len(vectors) if isinstance(vectors, list) else type(vectors)}',
            )
        return vectors
