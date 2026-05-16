# DocuChat

<img width="1376" height="768" alt="image" src="https://github.com/user-attachments/assets/1696de08-53fa-4d06-992f-5c414f6b1810" />


**Chat with your documents.** Upload PDFs and DOCX files, then ask questions and get streamed answers with inline source citations grounded in the document text — not the model's prior knowledge.

Built as a portfolio reference for a production-leaning RAG stack: typed Python on the backend, typed Next.js on the frontend, pluggable LLM providers, and a deploy story that fits free-tier infrastructure.

---

## What works today

- **Multi-tenant auth.** JWT in httpOnly cookies (`access_token` + `refresh_token`), bcrypt password hashing, cross-origin-friendly (Vercel ↔ Render). Refresh-on-401 axios interceptor on the frontend. `bcrypt` used directly because passlib is incompatible with bcrypt 5.x.
- **Document ingestion pipeline.** Upload → extract (pypdf / python-docx) → token-aware recursive chunking (tiktoken, 1000 tokens / 200 overlap) → embed (OpenAI `text-embedding-3-small`, batched with retry) → store in pgvector. Status transitions live on the row (`processing → extracting → chunking → embedding → ready` / `failed`). Pipeline runs in a background task with its own DB session.
- **RAG chat with streaming citations.** pgvector cosine-distance search filtered by document ownership, then OpenAI/Anthropic streams tokens over SSE. The system prompt enforces a `[Source: filename, Page X]` citation contract that the frontend parses to render a source panel. Conversation history is included in the LLM context.
- **Pluggable providers.** Storage is `local` or `s3`-compatible (Cloudflare R2 in prod). LLM is `openai` or `anthropic`. Embedding is `openai`. All selected via env vars; factories are cached.
- **Async end-to-end.** Async SQLAlchemy 2.0 throughout. OpenAI embeddings use `asyncio.to_thread`; LLM streaming uses `AsyncOpenAI` / `AsyncAnthropic` natively. The event loop stays responsive through both phases.
- **Operational hygiene.** Structured error responses (`{detail: {code, message}}`), request-ID middleware, per-user in-memory rate limiting on chat, startup reconciliation that flips abandoned-pipeline docs to `failed` after a restart.
- **Tested.** 80+ backend tests (pytest + pytest-asyncio), including authorization tests covering the IDOR boundary and the JWT default-secret guardrail. CI runs them against Postgres+pgvector so vector search is exercised, not skipped.

## Stack

| Layer | Choice | Why |
|------|--------|-----|
| Frontend | Next.js 16 App Router + TypeScript + Tailwind v4 + shadcn/ui | Familiar to most reviewers; route groups give a clean split between landed and authenticated UI. |
| Backend | FastAPI + async SQLAlchemy 2.0 | Async everywhere, type-checked, OpenAPI free. |
| Vector store | pgvector on Postgres | One database. No separate vector store to keep in sync. Cosine distance via the `<=>` operator. |
| Storage | Local disk or S3-compatible | R2 in prod (10GB free, S3 API). |
| LLM | OpenAI or Anthropic | Swap via `LLM_PROVIDER` env var. |
| Auth | JWT (httpOnly cookies) + bcrypt | Cookies for browser, `Authorization: Bearer` for tests. |
| Migrations | Alembic | Most schema work runs through `Base.metadata.create_all` at startup; Alembic kicks in when versioning matters. |
| CI | GitHub Actions | Postgres+pgvector service container so vector tests actually run. |
| Deploy | Render (backend) + Vercel (frontend) + Neon (Postgres) + Cloudflare R2 | All free tier. |

## Quick start

### Local — Docker Compose

The fastest path. Brings up Postgres+pgvector, the FastAPI backend, and the Next.js frontend together.

```bash
cp .env.example .env
# fill in OPENAI_API_KEY (and ANTHROPIC_API_KEY if you want to use Claude)
docker compose up
```

Frontend: <http://localhost:3000>. Backend: <http://localhost:8000>. API docs: <http://localhost:8000/api/docs>.

### Local — without Docker

Python 3.12 is required (3.14 breaks ChromaDB-era deps in the pin). pnpm for the frontend (npm has cache permission issues on some macs).

**Backend:**

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
pnpm install
pnpm dev
```

By default the backend uses SQLite (`./docuchat.db`). pgvector search only works on Postgres — point `DATABASE_URL` at one if you need to test that path locally.

### Tests + lint

```bash
# Backend
cd backend
pytest tests/                     # full suite
ruff check app/ tests/

# Frontend
cd frontend
pnpm lint
pnpm build
```

To exercise the pgvector tests locally, point a Postgres instance at the test runner:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docuchat_test \
  pytest tests/test_vector_store.py -v
```

## Architecture in one diagram

```
┌──────────────┐         ┌──────────────────────┐        ┌──────────────┐
│  Next.js     │  HTTPS  │  FastAPI             │  SQL   │  Postgres    │
│  Vercel      ├────────▶│  Render              ├───────▶│  Neon        │
│  • App Router│ cookies │  • Async SQLAlchemy  │ async  │  • pgvector  │
│  • TanStack  │         │  • SSE streaming     │ pg     │  • cosine    │
│  • shadcn/ui │◀────────┤  • JWT auth          │        │              │
└──────────────┘   SSE   │  • Rate limiter      │        └──────────────┘
                         │  • Request IDs       │
                         └──────────┬───────────┘
                                    │
                  ┌─────────────────┴──────────────────┐
                  ▼                                    ▼
        ┌──────────────────┐                ┌─────────────────────┐
        │  Cloudflare R2   │                │  OpenAI / Anthropic │
        │  • Uploaded PDFs │                │  • Embeddings       │
        │  • S3-compatible │                │  • Streamed chat    │
        └──────────────────┘                └─────────────────────┘
```

## Deployment

Render auto-deploys on push to `main` for the backend. Vercel does the same for the frontend. See `docs/deploy-batch-1.md` and `docs/deploy-batch-2.md` for runbooks on specific operational changes that have shipped.

Cross-origin auth needs `COOKIE_SAMESITE=none` and `COOKIE_SECURE=true` on Render, plus `NEXT_PUBLIC_API_URL=https://your-api.onrender.com/api` on Vercel (baked at build time — redeploy without build cache if you change it).

## Production considerations

This is a portfolio app on a free tier. If you were running it for real, the following would change:

- **Background work belongs on a queue.** Today the pipeline runs in `asyncio.create_task` and dies with the dyno. A worker pool (RQ / Arq / Dramatiq, or a hosted SQS+Lambda) survives restarts and gives you retries, dead-letter, and observability. Startup reconciliation papers over the gap; a queue removes it.
- **Rate limiting is in-memory.** Fine for one Render worker. With multiple workers or any horizontal scale, move to Redis-backed counters (or a managed gateway like Cloudflare).
- **pgvector needs an index above a few thousand rows.** The current setup runs sequential scans. At scale, add an HNSW index (`CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops)`) and tune `ef_search`.
- **Embedding/LLM clients aren't observable.** No timing histograms, no per-provider error counters, no retry telemetry. A real prod would add OpenTelemetry traces around every external call and a budget alert on token spend.
- **Auth refresh is single-token.** Refresh tokens are stored in a table but there's no per-device revocation UI. For real users you'd want a session list, a "log out everywhere" button, and IP/UA fingerprinting on refresh.
- **No content scanning.** Uploaded PDFs are trusted to be benign. A real prod would run AV scanning (ClamAV / cloud equivalent) and validate file structure before extraction.
- **Storage uses pre-signed URL bypass.** Right now the backend reads uploaded files itself. For large files you'd want direct-to-R2 uploads with pre-signed PUT URLs to keep the dyno out of the data path.
- **Eval is missing.** No golden Q&A set, no retrieval recall@k metric, no LLM judge. The next meaningful step is a small evaluation harness that catches retrieval regressions on commit.

## Project structure

```
docuchat/
├── backend/            # FastAPI + async SQLAlchemy
│   ├── app/
│   │   ├── routers/    # auth, documents, chat, chunks, conversations
│   │   ├── services/   # storage, extractor, chunker, embedder, vector_store, llm, rag, pipeline
│   │   ├── models/     # user, document, chunk, conversation
│   │   └── main.py     # FastAPI app, lifespan (pgvector ext + stuck-doc reconciliation)
│   ├── alembic/        # migrations
│   └── tests/          # 80+ tests; pgvector tests run when TEST_DATABASE_URL is set
├── frontend/           # Next.js 16 App Router + TypeScript
│   └── src/
│       ├── app/        # (app)/ route group is the authenticated UI
│       ├── components/ # shadcn/ui + custom
│       ├── contexts/   # auth context (TanStack Query + axios interceptor)
│       └── lib/        # api client with refresh-on-401
├── docs/
│   ├── CLAUDE.md       # canonical Claude Code project context (root CLAUDE.md is an @import pointer)
│   ├── build-plan.md   # original 10-stage build plan
│   ├── deploy-batch-1.md
│   └── deploy-batch-2.md
├── docker-compose.yml  # Postgres+pgvector + backend + frontend
└── .github/workflows/ci.yml  # Postgres service container, ruff + pytest + Next.js build
```

## License

MIT.
