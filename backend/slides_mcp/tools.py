"""MCP tool functions for the Google Slides MCP server.

Tools check that required inputs are present, then delegate to
``GoogleSlidesService``. Layouts, image URLs, and slide contents are
checked there. ``SlidesToolError`` is what the model reads when a call
cannot be completed.
"""

from typing import TypedDict

from mcp.server.mcpserver.exceptions import ToolError

from google_integration.services.google_auth import GoogleAuthError
from google_integration.services.google_slides import (
    GoogleSlidesError,
    google_slides_service,
)


class SlidesToolError(ToolError):
    """A tool failure the model can read and correct.

    The MCP server returns this message as the tool error text.
    """


class CreatedPresentation(TypedDict):
    presentation_id: str
    url: str


class CreatedSlide(TypedDict):
    presentation_id: str
    slide_id: str
    layout: str


class UpdatedSlide(TypedDict):
    presentation_id: str
    slide_id: str
    updated_fields: list[str]


class DeletedSlide(TypedDict):
    presentation_id: str
    slide_id: str


class DeletedPresentation(TypedDict):
    presentation_id: str
    deleted: bool


class AddedText(TypedDict):
    presentation_id: str
    slide_id: str
    object_id: str


class AddedImage(TypedDict):
    presentation_id: str
    slide_id: str
    object_id: str


def ping() -> str:
    """Check that the SmartClass Google Slides MCP server is reachable."""
    return 'pong'


def create_presentation(title: str) -> CreatedPresentation:
    """Create a Google Slides presentation viewable by anyone with the link.

    Returns the new presentation's ID and its edit URL.
    """
    title = _text(title, 'title')
    return _call(lambda: google_slides_service.create_presentation(title))


def get_presentation(presentation_id: str) -> dict:
    """Read a presentation's title, URL, and its slides.

    Each slide includes its ID, zero-based index, text, and image URLs.
    Slide count and text vary, so this tool has no fixed output schema.
    Callers read the JSON object from the tool result.
    """
    presentation_id = _text(presentation_id, 'presentation_id')
    return _call(lambda: google_slides_service.get_presentation(presentation_id))


def delete_presentation(presentation_id: str) -> DeletedPresentation:
    """Permanently delete a presentation. Deleting one that is already gone succeeds."""
    presentation_id = _text(presentation_id, 'presentation_id')
    return _call(lambda: google_slides_service.delete_presentation(presentation_id))


def add_slide(presentation_id: str, layout: str | None = None) -> CreatedSlide:
    """Append a slide to a presentation and return its ID.

    ``layout`` is an optional predefined layout and defaults to BLANK.
    Allowed values: BLANK, CAPTION_ONLY, TITLE, TITLE_AND_BODY,
    TITLE_AND_TWO_COLUMNS, TITLE_ONLY, SECTION_HEADER,
    SECTION_TITLE_AND_DESCRIPTION, ONE_COLUMN_TEXT, MAIN_POINT, BIG_NUMBER.
    """
    presentation_id = _text(presentation_id, 'presentation_id')
    return _call(lambda: google_slides_service.add_slide(presentation_id, layout))


def update_slide(
    presentation_id: str,
    slide_id: str,
    title: str | None = None,
    body: str | None = None,
) -> UpdatedSlide:
    """Set a slide's title, body, or both.

    Uses the layout's title and body placeholders when the slide has them.
    Otherwise creates a text box and replaces that same box on later calls.
    At least one of ``title`` or ``body`` is required.
    """
    presentation_id = _text(presentation_id, 'presentation_id')
    slide_id = _text(slide_id, 'slide_id')
    title = _optional_text(title, 'title')
    body = _optional_text(body, 'body')
    return _call(lambda: google_slides_service.update_slide(
        presentation_id, slide_id, title=title, body=body,
    ))


def delete_slide(presentation_id: str, slide_id: str) -> DeletedSlide:
    """Delete a slide from a presentation."""
    presentation_id = _text(presentation_id, 'presentation_id')
    slide_id = _text(slide_id, 'slide_id')
    return _call(lambda: google_slides_service.delete_slide(presentation_id, slide_id))


def add_text(presentation_id: str, slide_id: str, text: str) -> AddedText:
    """Add a text box to a slide and return the new object's ID."""
    presentation_id = _text(presentation_id, 'presentation_id')
    slide_id = _text(slide_id, 'slide_id')
    text = _text(text, 'text')
    return _call(lambda: google_slides_service.add_text(presentation_id, slide_id, text))


def add_image(
    presentation_id: str,
    slide_id: str,
    image_url: str,
) -> AddedImage:
    """Add an image from a public http(s) URL to a slide.

    Returns the new image object's ID. Google fetches the URL once, so it
    must be publicly reachable and be a PNG, JPEG, or GIF under 50 MB.
    """
    presentation_id = _text(presentation_id, 'presentation_id')
    slide_id = _text(slide_id, 'slide_id')
    image_url = _text(image_url, 'image_url')
    return _call(lambda: google_slides_service.add_image(
        presentation_id, slide_id, image_url,
    ))


def _text(value: str, name: str) -> str:
    text = (value or '').strip()
    if not text:
        raise SlidesToolError(f'{name} must be a non-empty string.')
    return text


def _optional_text(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _call(action):
    try:
        return action()
    except GoogleAuthError as exc:
        raise SlidesToolError(f'Google authentication failed: {exc}') from exc
    except GoogleSlidesError as exc:
        message = str(exc)
        if exc.presentation_id:
            message += (
                f' The presentation was created with ID {exc.presentation_id}.'
            )
        raise SlidesToolError(message) from exc
