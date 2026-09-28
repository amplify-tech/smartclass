"""Google Slides presentation operations for the shared Google account.

Authentication comes from ``google_auth_service``. Sharing uses the Drive
API because the Slides API cannot change file permissions, so the OAuth
token needs the ``presentations`` scope plus ``drive.file`` (or ``drive``).
"""

import logging

from googleapiclient.errors import HttpError
from httplib2 import HttpLib2Error

from google_integration.services.google_auth import google_auth_service

logger = logging.getLogger(__name__)

PRESENTATION_URL = 'https://docs.google.com/presentation/d/{presentation_id}/edit'


class GoogleSlidesError(Exception):
    """A Google Slides or Drive API call failed.

    ``presentation_id`` is set when the presentation was created but a
    later step (sharing) failed, so callers can still reach the file.
    """

    def __init__(self, message, presentation_id=None):
        super().__init__(message)
        self.presentation_id = presentation_id


class GoogleSlidesService:
    """Create and share Google Slides presentations.

    Raises ``GoogleAuthError`` when credentials are missing or the token
    refresh fails, and ``GoogleSlidesError`` when a Google API call fails.
    """

    def __init__(self, auth_service=google_auth_service):
        self._auth = auth_service

    def create_presentation(self, title):
        """Create a presentation, share it publicly, and return its ID and URL."""
        title = (title or '').strip()
        if not title:
            raise GoogleSlidesError('A presentation title is required.')

        slides = self._auth.get_api_client('slides', 'v1')
        presentation = _execute(
            slides.presentations().create(body={'title': title}),
            'create presentation',
        )
        presentation_id = presentation['presentationId']

        self.make_public(presentation_id)

        return {
            'presentation_id': presentation_id,
            'url': PRESENTATION_URL.format(presentation_id=presentation_id),
        }

    def make_public(self, presentation_id):
        """Let anyone with the link view the presentation."""
        drive = self._auth.get_api_client('drive', 'v3')
        try:
            _execute(
                drive.permissions().create(
                    fileId=presentation_id,
                    body={'type': 'anyone', 'role': 'reader'},
                    fields='id',
                ),
                'share presentation',
            )
        except GoogleSlidesError as exc:
            exc.presentation_id = presentation_id
            raise


def _execute(request, action):
    try:
        return request.execute()
    except HttpError as exc:
        detail = f'HTTP {exc.status_code}: {exc.reason}'
        logger.warning('Google API failed to %s: %s', action, detail)
        raise GoogleSlidesError(f'Failed to {action} ({detail}).') from exc
    except (HttpLib2Error, OSError) as exc:
        logger.warning('Google API request to %s failed: %s', action, exc)
        raise GoogleSlidesError(
            f'Failed to {action}: could not reach Google.'
        ) from exc


google_slides_service = GoogleSlidesService()
