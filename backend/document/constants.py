"""Document-domain constants shared by serializers and views."""

from common.constants import EMBEDDING_DIMENSIONS

ALLOWED_CONTENT_TYPES = frozenset({
    'application/pdf',
    'text/plain',
})

ALLOWED_EXTENSIONS = frozenset({'.pdf', '.txt'})

# 10 MiB
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

__all__ = [
    'ALLOWED_CONTENT_TYPES',
    'ALLOWED_EXTENSIONS',
    'EMBEDDING_DIMENSIONS',
    'MAX_UPLOAD_SIZE_BYTES',
]
