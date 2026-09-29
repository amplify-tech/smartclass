# SmartClass — Core Backend Architecture

Scope: Django/DRF backend only. MCP → `architecture-mcp.md`. RAG → `architecture-rag.md`.

## System Architecture

```text
Client (JWT Bearer)
  ↓
Django REST Framework   /api/v1/*   (SimpleJWT auth, IsAuthenticated default)
  ↓
ViewSets + Serializers  (routing, validation, owner-scoped querysets)
  ↓
Service layer           (ExamService, QuestionGenerationService, DocumentProcessingService,
  │                      ChatService, PresentationService, task.services)
  ↓
Django ORM ──────────────► PostgreSQL (+ pgvector)
  │
  ├─► File storage   (S3-compatible via django-storages, else local MEDIA_ROOT)
  ├─► LLMProvider    (Ollama | Gemini)                 via common/llm
  └─► Slides MCP client ► Slides MCP server ► Google APIs   (see architecture-mcp.md)

Background:  task.Job (DB row) ─► in-process ThreadPoolExecutor(2) ─► task handler
```

## Main Components

| Component | Responsibility |
|---|---|
| Django apps | `user`, `document`, `exam`, `task`, `chat`, `presentation`, `google_integration`; shared `common`, `config` |
| API layer | DRF ViewSets/serializers: routing, input validation, permissions, HTTP status mapping |
| Service layer | All business logic and orchestration; views stay thin |
| Data access | Django ORM used directly inside services (no separate repository layer) |
| Database | PostgreSQL only (all environments); pgvector for `DocumentChunk.embedding` |
| Authentication | JWT (`SimpleJWT`, 12h access / 7d refresh); email-based `User`; ownership enforced in `get_queryset()` |
| Background jobs | Generic `task.Job` + in-process thread pool; handlers registered in `TASK_HANDLER_MAPPING` |
| External integrations | LLM (Ollama/Gemini over HTTP), Google Slides/Drive (via MCP only), S3-compatible storage |
| `slides_mcp` | Standalone MCP server package (not a Django app) |

## Main Request Flow

```text
Client
 → URL router (config/urls.py → app urls)
 → JWTAuthentication + IsAuthenticated (+ IsOwnerOrReadOnly on Question)
 → Serializer validation (types, file size/extension, counts, ownership of document_ids)
 → View → Service
 → ORM (owner-scoped queryset / transaction.atomic)
 → PostgreSQL
 → Serializer → JSON response
```

## Background Job Flow

Two job types use it: `GENERATE_QUESTIONS`, `PROCESS_DOCUMENT_FOR_RAG`.

```text
Client POST (question-generation-jobs | documents)
 → validate (documents must be owned by user and READY)
 → create_and_submit_job(): Job(status=pending, payload, created_by)
 → return 201 + job (job_id)
 → ThreadPoolExecutor → run_job(job_id, request_user_id)
      guard: skip if RUNNING/COMPLETED; owner must match created_by
      status=running → handler(job_id, **payload)
      → completed + result   |   failed + client-safe error
 → Client polls GET question-generation-jobs/{id} or tasks/jobs/{id}
 → POST tasks/jobs/{id}/retry → reset to pending, retry_count+1 (max 3)
```

Inside `GENERATE_QUESTIONS` (`QuestionGenerationService.run_generation`):

```text
load Grade/Subject from payload
 → _build_generation_prompts
      no documents  → SYSTEM_PROMPT + user prompt
      documents     → RetrievalService → build_rag_context → RAG_SYSTEM_PROMPT   (architecture-rag.md)
 → LLMProvider.generate(response_format=JSON)
 → parse_questions()   (extract JSON, validate/normalize each question)
 → _save_questions()   (atomic: replace job's questions, options, labels)
 → Job.result = {question_ids}
```

`PROCESS_DOCUMENT_FOR_RAG`: `DocumentProcessingService` (see RAG file); document upload creates this job.

## Important Design Patterns

- **Service layer** — keeps views thin; orchestration lives in `*Service` classes.
- **Provider abstraction + Factory** — `LLMProvider` / `get_llm_provider()` swaps Ollama/Gemini via `LLM_PROVIDER` for both generation and embeddings.
- **Strategy** — `ChatHandler` per `chat_type`; file extractors chosen by extension.
- **Registry / command dispatch** — `TASK_HANDLER_MAPPING` maps `task_type` → handler so one `Job` table serves all background work.
- **Facade** — `QuestionGenerationJobViewSet` exposes `task.Job` in a domain-specific shape.
- **Adapter** — `GoogleSlidesService` (Google API) and `SlidesMCPClient` (MCP) isolate third-party APIs.
- **Plan-then-execute** — LLM output is a validated plan (`presentation/plan.py`); deterministic code runs it.

## Responsibility Boundaries

| Concern | Owner |
|---|---|
| HTTP/API, validation, permissions | ViewSets, serializers, `permissions.py` |
| Business logic | `*/services.py` |
| Background execution | `task/services.py` (submit), `task/task_runner.py` (execute + status) |
| LLM interaction | `common/llm/*` (transport); prompts in `exam/utils/prompts`, `presentation/prompts.py`; output parsing in `exam/utils/llm_json.py`, `presentation/plan.py` |
| External API calls (Google) | `google_integration/services/*` via `slides_mcp` tools; called from Django only through `SlidesMCPClient` |
| Database access | Django ORM inside services/views |
| File storage | Django `FileField` + `django-storages` |

## Failure Boundaries

| Failure | Current handling |
|---|---|
| API failure | DRF exceptions → HTTP status; `ConflictError` (409) for state conflicts; `Presentation*` exceptions map to 502/503 |
| DB failure | Multi-row writes use `transaction.atomic`; `Exam` edits use `select_for_update`. No explicit DB-outage handling. |
| LLM failure | In jobs: caught → `TaskFailed` with safe message (generic / parse / timeout) → `Job.failed`. `LLM_TIMEOUT=120s`. No automatic retry. |
| External API failure | Google errors surface through MCP tool errors (see MCP file). Embedding/LLM HTTP errors wrapped as domain errors. |
| Background job failure | `run_job` catches everything → `failed` + `error`; raw exception text never exposed; manual retry endpoint (max 3). Jobs are in-process: a crash/restart leaves rows `pending`/`running`. Not explicitly handled. |
| Invalid LLM output | `parse_questions` / `parse_plan` raise `ValueError`/`PlanError` → job failed / validation error. Minor normalization (difficulty, marks, MCQ correct option) instead of failing. |
| Retry / duplicate request | `run_job` ignores jobs already `RUNNING`/`COMPLETED`; `retry_job` rejects `RUNNING` and `retry_count ≥ 3`; `_save_questions` replaces prior questions for the same job. No idempotency key on job creation. |
