"""Google OAuth access-token cache for a single account.

Credentials come from the environment. The refresh token is sent only to
Google's token endpoint. API clients receive the access token alone.
"""

import logging
import os
import threading
import time

import requests

logger = logging.getLogger(__name__)

TOKEN_URL = 'https://oauth2.googleapis.com/token'
# Refresh slightly before Google's expiry so in-flight API calls still succeed.
EXPIRY_BUFFER_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 15

_REQUIRED_ENV_VARS = (
    'GOOGLE_CLIENT_ID',
    'GOOGLE_CLIENT_SECRET',
    'GOOGLE_REFRESH_TOKEN',
)


class GoogleAuthError(Exception):
    """Missing Google credentials or a failed access-token refresh."""


class GoogleAuthService:
    """Cache a Google access token and build API clients from it.

    Share one instance (``google_auth_service``) so the in-memory cache is
    reused across calls. This class does not depend on Django, so an MCP
    server can import it directly.
    """

    def __init__(self):
        self._access_token = None
        self._expires_at = None
        self._lock = threading.Lock()

    def get_access_token(self):
        """Return a valid access token, refreshing it when it is near expiry."""
        with self._lock:
            if self._token_is_valid():
                return self._access_token
            return self._refresh_access_token()

    def get_api_client(self, api_name, api_version):
        """Return a Google API client authenticated with a valid access token.

        ``api_name`` and ``api_version`` are discovery identifiers, for
        example ``slides`` / ``v1`` or ``drive`` / ``v3``. Only the access
        token is attached to the client.
        """
        if not api_name or not api_version:
            raise GoogleAuthError('api_name and api_version are required.')

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise GoogleAuthError(
                'Google API client libraries are not installed.'
            ) from exc

        credentials = Credentials(token=self.get_access_token())
        return build(
            api_name,
            api_version,
            credentials=credentials,
            cache_discovery=False,
        )

    def _token_is_valid(self):
        if not self._access_token or self._expires_at is None:
            return False
        return time.monotonic() < (self._expires_at - EXPIRY_BUFFER_SECONDS)

    def _refresh_access_token(self):
        client_id, client_secret, refresh_token = self._load_credentials()
        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token',
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            logger.warning('Google token endpoint request failed: %s', exc)
            raise GoogleAuthError(
                'Failed to reach the Google token endpoint.'
            ) from exc

        if response.status_code != 200:
            detail = _token_error_detail(response)
            logger.warning('Google token refresh failed: %s', detail)
            raise GoogleAuthError(f'Google token refresh failed: {detail}')

        access_token, expires_in = _parse_token_response(response)
        self._expires_at = time.monotonic() + expires_in
        self._access_token = access_token
        return self._access_token

    def _load_credentials(self):
        values = {
            name: os.environ.get(name, '').strip()
            for name in _REQUIRED_ENV_VARS
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise GoogleAuthError(
                'Missing required environment variables: ' + ', '.join(missing)
            )
        return (
            values['GOOGLE_CLIENT_ID'],
            values['GOOGLE_CLIENT_SECRET'],
            values['GOOGLE_REFRESH_TOKEN'],
        )


def _parse_token_response(response):
    try:
        payload = response.json()
    except ValueError as exc:
        raise GoogleAuthError(
            'Google token response was not valid JSON.'
        ) from exc

    if not isinstance(payload, dict):
        raise GoogleAuthError('Google token response had an unexpected shape.')

    access_token = payload.get('access_token')
    if not isinstance(access_token, str) or not access_token:
        raise GoogleAuthError(
            'Google token response did not include an access token.'
        )

    try:
        expires_in = int(payload['expires_in'])
    except (KeyError, TypeError, ValueError) as exc:
        raise GoogleAuthError(
            'Google token response did not include a valid expires_in value.'
        ) from exc

    if expires_in <= 0:
        raise GoogleAuthError(
            'Google token response included a non-positive expires_in value.'
        )

    return access_token, expires_in


def _token_error_detail(response):
    try:
        payload = response.json()
    except ValueError:
        return f'HTTP {response.status_code}'

    if not isinstance(payload, dict):
        return f'HTTP {response.status_code}'

    error = payload.get('error') or 'unknown_error'
    description = payload.get('error_description')
    if isinstance(description, str) and description:
        return f'{error}: {description}'
    return str(error)


# singe shared instance of the GoogleAuthService class
google_auth_service = GoogleAuthService()
