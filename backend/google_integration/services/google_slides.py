"""Google Slides presentation operations for the shared Google account.

Authentication comes from ``google_auth_service``. Sharing uses the Drive
API because the Slides API cannot change file permissions, so the OAuth
token needs the ``presentations`` scope plus ``drive.file`` (or ``drive``).
"""

import hashlib
import logging
import uuid

from googleapiclient.errors import HttpError
from httplib2 import HttpLib2Error

from google_integration.services.google_auth import google_auth_service

logger = logging.getLogger(__name__)

PRESENTATION_URL = 'https://docs.google.com/presentation/d/{presentation_id}/edit'

# Predefined layouts the Slides API accepts on createSlide.
PREDEFINED_LAYOUTS = (
    'BLANK',
    'CAPTION_ONLY',
    'TITLE',
    'TITLE_AND_BODY',
    'TITLE_AND_TWO_COLUMNS',
    'TITLE_ONLY',
    'SECTION_HEADER',
    'SECTION_TITLE_AND_DESCRIPTION',
    'ONE_COLUMN_TEXT',
    'MAIN_POINT',
    'BIG_NUMBER',
)

_TITLE_PLACEHOLDERS = ('TITLE', 'CENTERED_TITLE')
_BODY_PLACEHOLDERS = ('BODY', 'SUBTITLE')

# Points. The default page is 720 x 405.
_TEXT_BOXES = {
    'title': {'x': 36, 'y': 28, 'width': 648, 'height': 60},
    'body': {'x': 36, 'y': 108, 'width': 648, 'height': 250},
    'text': {'x': 36, 'y': 108, 'width': 648, 'height': 250},
}
_IMAGE_BOX = {'x': 380, 'y': 120, 'width': 280, 'height': 200}


class GoogleSlidesError(Exception):
    """A Google Slides or Drive API call failed.

    ``presentation_id`` is set when the presentation was created but a
    later step (sharing) failed, so callers can still reach the file.
    """

    def __init__(self, message, presentation_id=None):
        super().__init__(message)
        self.presentation_id = presentation_id


class GoogleSlidesService:
    """Read and edit Google Slides presentations for the shared account.

    Raises ``GoogleAuthError`` when credentials are missing or the token
    refresh fails, and ``GoogleSlidesError`` when a Google API call fails
    or a required argument is missing.
    """

    def __init__(self, auth_service=google_auth_service):
        self._auth = auth_service

    def create_presentation(self, title):
        """Create a presentation, share it publicly, and return its ID and URL."""
        title = _required(title, 'A presentation title is required.')

        slides = self._slides()
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

    def delete_presentation(self, presentation_id):
        """Delete the presentation file. A file that is already gone counts as deleted."""
        presentation_id = _required(
            presentation_id, 'A presentation ID is required.'
        )
        drive = self._auth.get_api_client('drive', 'v3')
        try:
            _execute(
                drive.files().delete(fileId=presentation_id),
                'delete presentation',
            )
        except GoogleSlidesError as exc:
            cause = exc.__cause__
            if not (isinstance(cause, HttpError) and cause.status_code == 404):
                raise
        return {'presentation_id': presentation_id, 'deleted': True}

    def get_presentation(self, presentation_id):
        """Return the presentation title, URL, and a summary of each slide."""
        presentation_id = _required(
            presentation_id, 'A presentation ID is required.'
        )
        presentation = _execute(
            self._slides().presentations().get(presentationId=presentation_id),
            'get presentation',
        )
        return _presentation_summary(presentation)

    def add_slide(self, presentation_id, layout=None):
        """Append a slide and return its ID. ``layout`` defaults to BLANK."""
        presentation_id = _required(
            presentation_id, 'A presentation ID is required.'
        )
        layout = _layout(layout)
        slide_id = _object_id('slide')
        _batch(
            self._slides(),
            presentation_id,
            [{
                'createSlide': {
                    'objectId': slide_id,
                    'slideLayoutReference': {'predefinedLayout': layout},
                },
            }],
            'add slide',
        )
        return {
            'presentation_id': presentation_id,
            'slide_id': slide_id,
            'layout': layout,
        }

    def update_slide(self, presentation_id, slide_id, title=None, body=None):
        """Set a slide's title and body text.

        Layout placeholders are updated when the slide has them. Otherwise
        a text box is created for that part and reused on later calls.
        """
        presentation_id = _required(
            presentation_id, 'A presentation ID is required.'
        )
        slide_id = _required(slide_id, 'A slide ID is required.')
        title = _optional_text(title, 'A title is required when provided.')
        body = _optional_text(body, 'A body is required when provided.')
        if title is None and body is None:
            raise GoogleSlidesError('A title or body is required.')

        client = self._slides()
        slide = _find_slide(
            _execute(
                client.presentations().get(presentationId=presentation_id),
                'get presentation',
            ),
            slide_id,
        )

        requests = []
        updated_fields = []
        if title is not None:
            requests.extend(_content_requests(
                slide, slide_id, 'title', title, _TITLE_PLACEHOLDERS,
            ))
            updated_fields.append('title')
        if body is not None:
            requests.extend(_content_requests(
                slide, slide_id, 'body', body, _BODY_PLACEHOLDERS,
            ))
            updated_fields.append('body')

        _batch(client, presentation_id, requests, 'update slide')
        return {
            'presentation_id': presentation_id,
            'slide_id': slide_id,
            'updated_fields': updated_fields,
        }

    def delete_slide(self, presentation_id, slide_id):
        """Delete a slide from the presentation."""
        presentation_id = _required(
            presentation_id, 'A presentation ID is required.'
        )
        slide_id = _required(slide_id, 'A slide ID is required.')
        _batch(
            self._slides(),
            presentation_id,
            [{'deleteObject': {'objectId': slide_id}}],
            'delete slide',
        )
        return {
            'presentation_id': presentation_id,
            'slide_id': slide_id,
        }

    def add_text(self, presentation_id, slide_id, text):
        """Add a text box to a slide and return the new object's ID."""
        presentation_id = _required(
            presentation_id, 'A presentation ID is required.'
        )
        slide_id = _required(slide_id, 'A slide ID is required.')
        text = _required(text, 'Text is required.')
        object_id = _object_id('txt')
        _batch(
            self._slides(),
            presentation_id,
            _create_text_box_requests(object_id, slide_id, text, _TEXT_BOXES['text']),
            'add text',
        )
        return {
            'presentation_id': presentation_id,
            'slide_id': slide_id,
            'object_id': object_id,
        }

    def add_image(self, presentation_id, slide_id, image_url):
        """Add an image from a public URL to a slide."""
        presentation_id = _required(
            presentation_id, 'A presentation ID is required.'
        )
        slide_id = _required(slide_id, 'A slide ID is required.')
        image_url = _image_url(image_url)
        object_id = _object_id('img')
        box = _IMAGE_BOX
        _batch(
            self._slides(),
            presentation_id,
            [{
                'createImage': {
                    'objectId': object_id,
                    'url': image_url,
                    'elementProperties': _element_properties(slide_id, box),
                },
            }],
            'add image',
        )
        return {
            'presentation_id': presentation_id,
            'slide_id': slide_id,
            'object_id': object_id,
        }

    def _slides(self):
        return self._auth.get_api_client('slides', 'v1')


def _required(value, message):
    value = (value or '').strip()
    if not value:
        raise GoogleSlidesError(message)
    return value


def _optional_text(value, message):
    if value is None:
        return None
    return _required(value, message)


def _layout(layout):
    if layout is None or not str(layout).strip():
        return 'BLANK'
    layout = str(layout).strip().upper()
    if layout not in PREDEFINED_LAYOUTS:
        allowed = ', '.join(PREDEFINED_LAYOUTS)
        raise GoogleSlidesError(
            f'Unknown slide layout {layout!r}. Expected one of: {allowed}.'
        )
    return layout


def _image_url(value):
    url = _required(value, 'An image URL is required.')
    if not url.startswith(('http://', 'https://')):
        raise GoogleSlidesError(
            'The image URL must start with http:// or https://.'
        )
    return url


def _object_id(prefix):
    return f'{prefix}_{uuid.uuid4().hex[:16]}'


def _content_object_id(slide_id, role):
    """Stable id so a later update replaces the box created earlier."""
    digest = hashlib.sha256(f'{role}:{slide_id}'.encode()).hexdigest()[:16]
    return f'{role}_{digest}'


def _presentation_summary(presentation):
    presentation_id = presentation.get('presentationId', '')
    slides = []
    for index, slide in enumerate(presentation.get('slides') or []):
        texts = []
        image_urls = []
        for element in slide.get('pageElements') or []:
            text = _element_text(element).strip()
            if text:
                texts.append(text)
            image = element.get('image') or {}
            url = image.get('sourceUrl') or image.get('contentUrl')
            if url:
                image_urls.append(url)
        slides.append({
            'slide_id': slide.get('objectId', ''),
            'index': index,
            'text': '\n'.join(texts),
            'image_urls': image_urls,
        })
    return {
        'presentation_id': presentation_id,
        'title': presentation.get('title') or '',
        'url': PRESENTATION_URL.format(presentation_id=presentation_id),
        'slides': slides,
    }


def _find_slide(presentation, slide_id):
    for slide in presentation.get('slides') or []:
        if slide.get('objectId') == slide_id:
            return slide
    raise GoogleSlidesError(
        f'Slide {slide_id!r} was not found in the presentation.'
    )


def _element_by_placeholder(slide, placeholder_types):
    for element in slide.get('pageElements') or []:
        shape = element.get('shape') or {}
        placeholder = (shape.get('placeholder') or {}).get('type')
        if placeholder in placeholder_types:
            return element
    return None


def _element_by_id(slide, object_id):
    for element in slide.get('pageElements') or []:
        if element.get('objectId') == object_id:
            return element
    return None


def _element_text(element):
    shape = element.get('shape') or {}
    parts = []
    for text_element in (shape.get('text') or {}).get('textElements') or []:
        content = (text_element.get('textRun') or {}).get('content')
        if content:
            parts.append(content)
    return ''.join(parts)


def _content_requests(slide, slide_id, role, text, placeholder_types):
    element = _element_by_placeholder(slide, placeholder_types)
    if element is None:
        element = _element_by_id(slide, _content_object_id(slide_id, role))
    if element is None:
        return _create_text_box_requests(
            _content_object_id(slide_id, role),
            slide_id,
            text,
            _TEXT_BOXES[role],
        )
    return _replace_text_requests(element['objectId'], text, _element_text(element))


def _replace_text_requests(object_id, text, current_text):
    requests = []
    if current_text:
        requests.append({
            'deleteText': {
                'objectId': object_id,
                'textRange': {'type': 'ALL'},
            },
        })
    requests.append({
        'insertText': {
            'objectId': object_id,
            'insertionIndex': 0,
            'text': text,
        },
    })
    return requests


def _create_text_box_requests(object_id, slide_id, text, box):
    return [
        {
            'createShape': {
                'objectId': object_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': _element_properties(slide_id, box),
            },
        },
        {
            'insertText': {
                'objectId': object_id,
                'insertionIndex': 0,
                'text': text,
            },
        },
    ]


def _element_properties(slide_id, box):
    return {
        'pageObjectId': slide_id,
        'size': {
            'width': {'magnitude': box['width'], 'unit': 'PT'},
            'height': {'magnitude': box['height'], 'unit': 'PT'},
        },
        'transform': {
            'scaleX': 1,
            'scaleY': 1,
            'translateX': box['x'],
            'translateY': box['y'],
            'unit': 'PT',
        },
    }


def _batch(client, presentation_id, requests, action):
    return _execute(
        client.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests},
        ),
        action,
    )


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
