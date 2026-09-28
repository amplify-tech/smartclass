from rest_framework import status
from rest_framework.exceptions import APIException


class SlidesUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Google Slides is unavailable right now. Please try again.'
    default_code = 'slides_unavailable'


class PlanGenerationFailed(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Could not plan the presentation changes. Please try again.'
    default_code = 'plan_generation_failed'


class PresentationCommandFailed(APIException):
    """A Slides MCP tool failed. Changes made before it are kept."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = 'presentation_command_failed'

    def __init__(self, detail, presentation=None, steps=None):
        super().__init__(detail)
        self.presentation = presentation
        self.steps = steps or []
