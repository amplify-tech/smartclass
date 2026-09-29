# SmartClass — MCP Architecture

Scope: the Google Slides MCP integration behind presentation chat.

Key design fact: the LLM does **not** use native tool-calling. It returns a JSON decision/plan; Django code validates it and calls MCP tools deterministically. Tool results are not fed back to the LLM; replies are templated by code.

## MCP Architecture

```text
Teacher
  ↓
React Chat
  ↓
POST /conversations/{id}/messages        (ConversationViewSet, synchronous)
  ↓
ChatService.send()  ── saves user message
  ↓
PresentationChatHandler.respond()
  ↓
LLM call #1 (CHAT_SYSTEM_PROMPT, JSON)  →  {action, presentation_id, instruction, reply}
  ↓
action: create | update | info | delete | reply
  ↓                                   (reply → text answer, no MCP)
PresentationService
  ↓
LLM call #2 (create/update only) → plan → parse_plan() validation
  ↓
SlidesMCPClient  (one MCP session per operation)
  ↓  stdio subprocess `python -m slides_mcp.server`  (or streamable-http via SLIDES_MCP_URL)
MCP Server  (slides_mcp.server.MCPServer)
  ↓
MCP Tool  (slides_mcp/tools.py: validate args)
  ↓
GoogleSlidesService  (google_integration/services)
  ↓
GoogleAuthService → access token
  ↓
Google Slides API v1  /  Google Drive API v3
  ↓
tool result (structured dict)
  ↓
PresentationService: record Presentation, re-read slides
  ↓
templated reply → assistant Message + Conversation.context
```

## Components

| Component | Implementation |
|---|---|
| Chat/API layer | `chat.views.ConversationViewSet`, `chat.services.ChatService` |
| Chat routing | `ChatHandler` strategy; `chat_type='presentation'` → `PresentationChatHandler` (lazy import) |
| LLM provider | `common.llm` (`get_llm_provider().generate(..., JSON)`) |
| Orchestrator | `presentation.services.PresentationService` |
| Plan validation | `presentation/plan.py` (`parse_plan`), prompts in `presentation/prompts.py` |
| MCP client | `google_integration.mcp_client.SlidesMCPClient` |
| MCP server | `slides_mcp/server.py` (`MCPServer`, stdio or streamable-http) |
| MCP tools | `slides_mcp/tools.py`: `ping`, `create_presentation`, `get_presentation`, `delete_presentation`, `add_slide`, `update_slide`, `delete_slide`, `add_text`, `add_image` |
| Google auth | `GoogleAuthService` (`google_auth.py`) |
| Google APIs | Slides (create/read/edit) and Drive (public-link permission, delete file) via `GoogleSlidesService` |
| Persistence | `Conversation` (`context` JSON), `Message`, `Presentation` (`google_presentation_id`, `url`, `created_by`) |

## Tool Calling Flow

Example: "Create a 5-slide deck on photosynthesis".

```text
User message
 → LLM #1 sees: latest message + previous 1 message + chat's presentations (IDs/titles)
 → action=create, instruction rewritten standalone
 → LLM #2 (CREATE_SYSTEM_PROMPT) → {intent:create, title, slides[{title, body, image_url?}]}
 → parse_plan(): title/slides required, ≤15 slides, text limits, image_url only if present in instruction
 → MCP session opens
      create_presentation(title)              → Slides create + Drive "anyone can view"
      get_presentation(id)                    → reuse the default title slide
      per slide: add_slide(layout) → update_slide(title, body) → add_image? 
      get_presentation(id)                    → final slides
 → Presentation row saved
 → reply: 'Created "<title>" with N slides. <url>'
```

Other actions:
- `update` → `get_presentation` for context → LLM #2 (`UPDATE_SYSTEM_PROMPT`) → actions `add_slide | update_slide | delete_slide | add_image` (≤20, slide numbers validated, resolved to `slide_id`s up front) → tool calls. If the plan says `create`, a new deck is made instead.
- `info` → `get_presentation` only (lists slides). `delete` → `delete_presentation` + delete row.

## Conversation Continuation

```text
Create PPT
   ↓
Conversation.context = {presentations:[{id,title,url}], active_presentation_id}
   ↓
User: "Change slide 2 title to X"
   ↓
history = previous 1 message (CHAT_HISTORY_LIMIT) + stored context
   ↓
LLM #1 → action=update, presentation_id (LLM choice → title match → sole presentation)
   ↓
get_presentation → LLM #2 plan → update_slide(slide_id, title)
   ↓
same Google deck updated; active_presentation_id refreshed
```

- Ambiguous target → code replies "Which presentation do you mean?" (no guess).
- Deleted presentations are dropped from context on next load.
- Memory is the stored context plus one previous message, not full history.

## MCP Responsibilities

```text
LLM                 → decides WHAT to do (action, then a slide plan). Never calls tools itself.
PresentationService → validates the plan, orders tool calls, tracks partial results
MCP client/server   → exposes and transports executable tools (list/call over MCP)
MCP tool            → checks required args, maps errors to SlidesToolError
GoogleSlidesService → builds Slides/Drive requests
Google API          → performs the actual operation
```

## Authentication Flow

```text
Env: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REFRESH_TOKEN  (single shared Google account)
 → tool → GoogleAuthService.get_access_token()
      cached token valid (60s buffer, lock-guarded)? use it
      else POST oauth2.googleapis.com/token (grant_type=refresh_token)
 → Credentials(token) → googleapiclient build('slides','v1' | 'drive','v3')
```

- Refresh token is used only against Google's token endpoint; API clients get the access token only.
- Not per-teacher OAuth: all decks are created in one server-side Google account; SmartClass ownership is `Presentation.created_by`.
- Decks are shared "anyone with link → reader".
- Django user auth (JWT) protects the chat API; MCP calls carry no user identity.

## Failure Boundaries

| Failure | Handling |
|---|---|
| LLM #1 call fails | `ValidationError` "Could not process your message" → saved as an error assistant message (`is_error=True`) |
| LLM #1 invalid JSON / unknown action | Falls back to `reply` action with a rephrase prompt |
| LLM #2 call fails | `PlanGenerationFailed` (502) → error message |
| Invalid plan | `PlanError` → `ValidationError` (bad slide number, no slides, >15 slides, missing image URL) |
| Invalid tool arguments | Tool raises `SlidesToolError` → `MCPToolError` |
| MCP server unreachable / connection lost | `MCPClientError` → `SlidesUnavailable` (503); if a deck already exists, `PresentationCommandFailed` with partial result |
| MCP tool error | `PresentationCommandFailed` (502); earlier steps are kept, no rollback; deck still recorded |
| Google auth failure | `GoogleAuthError` → tool error "Google authentication failed" |
| Google API failure | `GoogleSlidesError` (HTTP status text) → tool error; sharing failure reports the created deck ID |
| Timeout | `SLIDES_MCP_TIMEOUT_SECONDS` (60s) read timeout on MCP calls → `MCPClientError` |
| Non-API exception in handler | Not explicitly handled (user message is already saved; no rollback) |
