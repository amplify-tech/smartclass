"""Project-wide API exceptions. Prefer field validators for input shape."""

from rest_framework import status
from rest_framework.exceptions import APIException


class ConflictError(APIException):
    """Resource state prevents the requested change (HTTP 409)."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = (
        'The request conflicts with the current state of the resource.'
    )
    default_code = 'conflict'
