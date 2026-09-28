"""MCP tool functions for the Google Slides MCP server.

Tools stay thin: they validate MCP inputs and delegate Google Slides API
work to ``google_integration.services``.
"""

from typing import TypedDict

from mcp.server.mcpserver.exceptions import ToolError

from google_integration.services.google_auth import GoogleAuthError
from google_integration.services.google_slides import (
    GoogleSlidesError,
    google_slides_service,
)


class CreatedPresentation(TypedDict):
    presentation_id: str
    url: str


def ping() -> str:
    """Check that the SmartClass Google Slides MCP server is reachable."""
    return 'pong'


def create_presentation(title: str) -> CreatedPresentation:
    """Create a Google Slides presentation viewable by anyone with the link.

    Returns the new presentation's ID and its edit URL.
    """
    title = title.strip()
    if not title:
        raise ToolError('title must be a non-empty string.')

    try:
        result = google_slides_service.create_presentation(title)
    except GoogleAuthError as exc:
        raise ToolError(f'Google authentication failed: {exc}') from exc
    except GoogleSlidesError as exc:
        message = str(exc)
        if exc.presentation_id:
            message += f' The presentation was created with ID {exc.presentation_id}.'
        raise ToolError(message) from exc

    return CreatedPresentation(
        presentation_id=result['presentation_id'],
        url=result['url'],
    )
