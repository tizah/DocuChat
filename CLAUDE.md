# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DocuChat is a full-stack RAG (Retrieval-Augmented Generation) document Q&A app. Users upload PDFs/DOCX files and ask questions; the backend retrieves relevant chunks and streams an LLM answer with inline citations. Monorepo: `backend/` (FastAPI) + `frontend/` (Next.js). Build progress is tracked in `DOCUCHAT_BUILD_PLAN.md`.

## Commands

### Backend (run from `backend/`)

```bash
# First-time setup — Python 3.12 is required (3.14 incompatible with ChromaDB)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Dev server (hot reload)
uvicorn app.main:app --reload --port 8000

# Tests
pytest tests/ -v
pytest tests/test_chat.py::test_chat_streams_response -v   # single test
pytest tests/ -k "chunker" -v                              # filter by keyword

# Lint
ruff check app/ tests/
ruff check --fix app/ tests/

# DB migrations (SQLite via SQLAlchemy async)
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Note: `app/main.py` calls `Base.metadata.create_all` on startup, so the schema is auto-created for local dev. Use Alembic only when you need versioned migrations.

### Frontend (run from `frontend/`)

```bash
pnpm install     # npm has known cache permission issues on this machine — use pnpm
pnpm dev         # localhost:3000
pnpm lint
pnpm build
```

### Full stack via Docker

```bash
cp .env.example .env   # fill in OPENAI_API_KEY / ANTHROPIC_API_KEY
docker compose up
```

The compose stack runs Postgres+pgvector (`pgvector/pgvector:pg16`) alongside backend and frontend, and overrides `DATABASE_URL` to point at it — so `docker compose up` gives a full end-to-end RAG environment locally (chat works, vector search works). The `postgres_data` volume persists across `docker compose down`; use `docker compose down -v` to nuke it.

## Architecture

### RAG pipeline (the core flow)

Document ingestion runs as a background task kicked off from `POST /api/documents` (`app/routers/documents.py::_run_pipeline_background`). It uses its own `async_session` because the request's DB session is closed once the response returns. The pipeline stages live in `app/services/pipeline.py::process_document` and update `document.status` at each step: `processing` → `extracting` → `chunking` → `embedding` → `ready` (or `failed`).

Stage handlers:
- `services/storage.py` — pluggable file storage (`LocalStorage` writes to `upload_dir`; `S3Storage` is S3-compatible, used for Cloudflare R2). Selected by `STORAGE_BACKEND` env. `extractor` consumes bytes, not paths, so the pipeline stays storage-agnostic.
- `services/extractor.py` — PDF (pypdf) / DOCX (python-docx) on `bytes` → list of `(page_number, text)` pairs
- `services/chunker.py` — token-aware recursive splitter using tiktoken; configurable `chunk_size` / `chunk_overlap` in settings
- `services/embedder.py` — pluggable provider (currently OpenAI `text-embedding-3-small`, 1536 dims); batched with tenacity retry
- `services/vector_store.py` — **pgvector**, not a separate store. Embeddings live on the `chunks.embedding` column (`Vector(1536)` on Postgres, JSON variant on SQLite for tests). `search_chunks(db, query_embedding, document_ids, top_k)` runs an async SQLAlchemy query using pgvector's `<=>` cosine distance operator. Distance ([0, 2]) is converted to a 0–1 similarity score.

Chat flow (`app/routers/chat.py`):
1. Validate `document_ids`, check `chat_rate_limiter` (per-user, in-memory)
2. Create or load `Conversation`, save user `Message`
3. `services/rag.py::retrieve_chunks(db, ...)` → embed query, run pgvector cosine search filtered by `document_ids`
4. Commit DB state before streaming starts (so the conversation row exists if the client reconnects)
5. Return `EventSourceResponse` that yields `metadata` (conversation_id + source_chunks for citations), `token` events from `stream_rag_response`, then `done`
6. After stream completes, save assistant `Message` with `source_chunks` JSON in a separate transaction

The LLM provider is swappable via `LLM_PROVIDER=openai|anthropic` in `.env` — see `services/llm.py`. Both providers expose `stream_chat(system_prompt, messages) -> Generator[str]`.

The RAG system prompt (`services/rag.py::SYSTEM_PROMPT`) enforces the citation format `[Source: filename, Page X]` — the frontend parses these to render the source panel.

### Auth model

JWT in httpOnly cookies (`access_token`, `refresh_token`), with `Authorization: Bearer` fallback for tests/API clients. `app/dependencies.py::get_current_user` checks cookie first, then header. The `CurrentUser` annotated type is the standard way to require auth in route signatures. `frontend/src/lib/api.ts` has an axios interceptor that auto-calls `/auth/refresh` on 401 and retries the request once before redirecting to `/login`.

**bcrypt is used directly** (`app/services/auth.py`) — passlib is incompatible with bcrypt 5.x, so we skip the wrapper.

### Error handling contract

All custom errors derive from `app/exceptions.py::AppError` and return:
```json
{"detail": {"code": "ERROR_CODE", "message": "..."}}
```
The global handler in `main.py` formats these consistently. The frontend's `getErrorMessage()` in `lib/api.ts` knows this shape. Use `NotFoundError`, `ValidationError`, `ForbiddenError`, `RateLimitError`, `ConflictError` — don't raise raw `HTTPException`.

### Request logging

`RequestLoggingMiddleware` generates a UUID per request, attaches it as `X-Request-ID`, and logs method/path/status/duration. Useful for tracing across logs when debugging streaming or background pipeline issues.

### Frontend structure

Next.js 16 App Router. Route group `(app)/` wraps pages that need the sidebar layout (documents list, chat). The landing page `/`, `/login`, and `/register` are outside the group and have no sidebar.

- `lib/api.ts` — axios instance with `withCredentials: true` and the 401-refresh interceptor; **all API calls go through this**
- `contexts/auth-context.tsx` — wraps TanStack Query provider and exposes the current user
- `components/providers.tsx` — TanStack Query + Auth + Theme providers, mounted in root `layout.tsx`
- shadcn/ui components live in `components/ui/`; custom components in `components/`
- Dark mode via `next-themes`; toasts via `sonner`
- Streaming chat: the frontend reads SSE from `/api/chat` and accumulates tokens; metadata event carries `source_chunks` for the citation panel

### Tests

Pytest with `asyncio_mode = "auto"`. The shared `conftest.py` provides:
- `db_session` — isolated SQLite file per test, schema created/dropped
- `client` — `AsyncClient` with auth cookies (auto-registers `test@example.com`) and `_run_pipeline_background` mocked so upload tests don't hit OpenAI or the pipeline
- `unauth_client` — no auth, for testing 401s

When adding routes that need auth, prefer `client` over building a fixture; for endpoint-level 401 tests, use `unauth_client`.

`tests/test_vector_store.py` skips on SQLite because pgvector's `cosine_distance` is Postgres-only. To exercise it, point `DATABASE_URL` at a Postgres instance with the `vector` extension. Tests that need to mock `retrieve_chunks` must use `unittest.mock.AsyncMock` — it's an async function now.

## Conventions

- Backend uses **async SQLAlchemy 2.0** style throughout. Sessions are committed by the `get_db` dependency on successful response, rolled back on exception. For background tasks, open a fresh session via `async_session()` — don't reuse the request's.
- `Annotated[AsyncSession, Depends(get_db)]` → aliased as `DbSession` in routers; `CurrentUser` for auth.
- Ruff config selects `E, W, F, I, N, UP, B, SIM`. Line length 100. `app` is treated as first-party for isort.
- Environment variables override `Settings` defaults via pydantic-settings (`.env` file).
- The `[tool.setuptools.packages.find]` block in `pyproject.toml` is intentional — without `include = ["app*"]`, setuptools tries to package `uploads/` and `alembic/` and fails.
