"""MCP tool functions for the Google Slides MCP server.

Tools stay thin: they validate MCP inputs and delegate Google Slides API
work to ``google_integration.services``.
"""

from typing import TypedDict

from mcp.server.mcpserver.exceptions import ToolError

from google_integration.services.google_auth import GoogleAuthError
from google_integration.services.google_slides import (
    PREDEFINED_LAYOUTS,
    GoogleSlidesError,
    google_slides_service,
)


class CreatedPresentation(TypedDict):
    presentation_id: str
    url: str


class SlideInfo(TypedDict):
    slide_id: str
    index: int
    text: str
    image_urls: list[str]


class PresentationInfo(TypedDict):
    presentation_id: str
    title: str
    url: str
    slides: list[SlideInfo]


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
    title = _required_text(title, 'title')
    result = _call(lambda: google_slides_service.create_presentation(title))
    return CreatedPresentation(
        presentation_id=result['presentation_id'],
        url=result['url'],
    )


def get_presentation(presentation_id: str) -> PresentationInfo:
    """Read a presentation's title, URL, and its slides.

    Each slide includes its ID, zero-based index, text, and image URLs.
    """
    presentation_id = _required_text(presentation_id, 'presentation_id')
    result = _call(
        lambda: google_slides_service.get_presentation(presentation_id)
    )
    return PresentationInfo(
        presentation_id=result['presentation_id'],
        title=result['title'],
        url=result['url'],
        slides=[
            SlideInfo(
                slide_id=slide['slide_id'],
                index=slide['index'],
                text=slide['text'],
                image_urls=list(slide['image_urls']),
            )
            for slide in result['slides']
        ],
    )


def delete_presentation(presentation_id: str) -> DeletedPresentation:
    """Permanently delete a presentation. Deleting one that is already gone succeeds."""
    presentation_id = _required_text(presentation_id, 'presentation_id')
    result = _call(
        lambda: google_slides_service.delete_presentation(presentation_id)
    )
    return DeletedPresentation(
        presentation_id=result['presentation_id'],
        deleted=result['deleted'],
    )


def add_slide(presentation_id: str, layout: str | None = None) -> CreatedSlide:
    """Append a slide to a presentation and return its ID.

    ``layout`` is an optional predefined layout and defaults to BLANK.
    Allowed values: BLANK, CAPTION_ONLY, TITLE, TITLE_AND_BODY,
    TITLE_AND_TWO_COLUMNS, TITLE_ONLY, SECTION_HEADER,
    SECTION_TITLE_AND_DESCRIPTION, ONE_COLUMN_TEXT, MAIN_POINT, BIG_NUMBER.
    """
    presentation_id = _required_text(presentation_id, 'presentation_id')
    if layout is not None:
        layout = layout.strip().upper()
        if layout not in PREDEFINED_LAYOUTS:
            allowed = ', '.join(PREDEFINED_LAYOUTS)
            raise ToolError(f'layout must be one of: {allowed}.')
    result = _call(
        lambda: google_slides_service.add_slide(presentation_id, layout)
    )
    return CreatedSlide(
        presentation_id=result['presentation_id'],
        slide_id=result['slide_id'],
        layout=result['layout'],
    )


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
    presentation_id = _required_text(presentation_id, 'presentation_id')
    slide_id = _required_text(slide_id, 'slide_id')
    title = _optional_text(title, 'title')
    body = _optional_text(body, 'body')
    if title is None and body is None:
        raise ToolError('title or body is required.')
    result = _call(lambda: google_slides_service.update_slide(
        presentation_id, slide_id, title=title, body=body,
    ))
    return UpdatedSlide(
        presentation_id=result['presentation_id'],
        slide_id=result['slide_id'],
        updated_fields=list(result['updated_fields']),
    )


def delete_slide(presentation_id: str, slide_id: str) -> DeletedSlide:
    """Delete a slide from a presentation."""
    presentation_id = _required_text(presentation_id, 'presentation_id')
    slide_id = _required_text(slide_id, 'slide_id')
    result = _call(
        lambda: google_slides_service.delete_slide(presentation_id, slide_id)
    )
    return DeletedSlide(
        presentation_id=result['presentation_id'],
        slide_id=result['slide_id'],
    )


def add_text(presentation_id: str, slide_id: str, text: str) -> AddedText:
    """Add a text box to a slide and return the new object's ID."""
    presentation_id = _required_text(presentation_id, 'presentation_id')
    slide_id = _required_text(slide_id, 'slide_id')
    text = _required_text(text, 'text')
    result = _call(
        lambda: google_slides_service.add_text(presentation_id, slide_id, text)
    )
    return AddedText(
        presentation_id=result['presentation_id'],
        slide_id=result['slide_id'],
        object_id=result['object_id'],
    )


def add_image(
    presentation_id: str,
    slide_id: str,
    image_url: str,
) -> AddedImage:
    """Add an image from a public http(s) URL to a slide.

    Returns the new image object's ID. Google fetches the URL once, so it
    must be publicly reachable and be a PNG, JPEG, or GIF under 50 MB.
    """
    presentation_id = _required_text(presentation_id, 'presentation_id')
    slide_id = _required_text(slide_id, 'slide_id')
    image_url = _required_text(image_url, 'image_url')
    if not image_url.startswith(('http://', 'https://')):
        raise ToolError('image_url must be an http or https URL.')
    result = _call(lambda: google_slides_service.add_image(
        presentation_id, slide_id, image_url,
    ))
    return AddedImage(
        presentation_id=result['presentation_id'],
        slide_id=result['slide_id'],
        object_id=result['object_id'],
    )


def _required_text(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise ToolError(f'{name} must be a non-empty string.')
    return value


def _optional_text(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, name)


def _call(action):
    try:
        return action()
    except GoogleAuthError as exc:
        raise ToolError(f'Google authentication failed: {exc}') from exc
    except GoogleSlidesError as exc:
        message = str(exc)
        if exc.presentation_id:
            message += (
                f' The presentation was created with ID {exc.presentation_id}.'
            )
        raise ToolError(message) from exc
