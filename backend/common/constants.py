MAX_RETRIES = 3

GENERATE_QUESTIONS = 'GENERATE_QUESTIONS'
PROCESS_DOCUMENT_FOR_RAG = 'PROCESS_DOCUMENT_FOR_RAG'

TEXT = 'text'
JSON = 'json'

# Seconds for LLM HTTP calls (Ollama / Gemini).
LLM_TIMEOUT = 120

# RAG — chunking + retrieval (embeddings are 768-dim; see DocumentChunk)
EMBEDDING_DIMENSIONS = 768
# Local (Ollama) default; Gemini uses settings.EMBEDDING_MODEL or text-embedding-004.
RAG_EMBEDDING_MODEL = 'nomic-embed-text'
# Max texts per provider.embed() call (Gemini batchEmbedContents limit is 100).
RAG_EMBEDDING_BATCH_SIZE = 100
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 5
RAG_SIMILARITY_THRESHOLD = 0.7
# Max characters of retrieved chunk text injected into an LLM prompt.
RAG_CONTEXT_LIMIT = 4000
