MAX_RETRIES = 3

GENERATE_QUESTIONS = 'GENERATE_QUESTIONS'

TEXT = 'text'
JSON = 'json'

# Seconds for LLM HTTP calls (Ollama / Gemini).
LLM_TIMEOUT = 120

# RAG — chunking + retrieval (embeddings are 768-dim; see DocumentChunk)
# Default matches a common 768-dim local model (e.g. Ollama nomic-embed-text).
RAG_EMBEDDING_MODEL = 'nomic-embed-text'
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_TOP_K = 5
RAG_SIMILARITY_THRESHOLD = 0.7
# Max characters of retrieved chunk text injected into an LLM prompt.
RAG_CONTEXT_LIMIT = 4000
