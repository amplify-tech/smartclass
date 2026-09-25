"""Document-domain constants shared by serializers and views."""

ALLOWED_CONTENT_TYPES = frozenset({
    'application/pdf',
    'text/plain',
})

ALLOWED_EXTENSIONS = frozenset({'.pdf', '.txt'})

# 10 MiB
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

# Must match DocumentChunk.embedding VectorField dimensions and the
# embedding model in common.constants.RAG_EMBEDDING_MODEL.
EMBEDDING_DIMENSIONS = 768
