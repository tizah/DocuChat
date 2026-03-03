# DocuChat — Claude Code Build Plan

> **Purpose:** You are building "DocuChat," an open-source RAG (Retrieval-Augmented Generation) document Q&A application. This is a portfolio-grade project for a Senior Full-Stack Engineer with AI/ML experience. Every stage must be committed independently with a clean, descriptive commit message so the Git history tells a professional story of incremental progress.

---

## Global Rules (Apply to Every Stage)

1. **Commit after every stage.** Use conventional commits: `feat:`, `chore:`, `fix:`, `docs:`, `test:`, `ci:`. Each commit message should be descriptive (e.g., `feat: add PDF/DOCX upload with drag-and-drop UI`), not generic.
2. **TypeScript strict mode** for all frontend code. Python type hints throughout backend code.
3. **Write tests alongside features** — not as an afterthought. Each stage that adds logic must include relevant unit/integration tests.
4. **README.md** must be updated at the end of every stage to reflect what currently works.
5. **No secrets in code.** Use `.env` files (with `.env.example` committed) from the start.
6. **Linting and formatting:** ESLint + Prettier for frontend, Ruff for backend. Configure in Stage 1.
7. **Error handling:** Every API endpoint returns structured error responses. Every frontend API call has loading/error states.
8. **Accessibility:** All interactive elements must have proper ARIA labels and keyboard navigation.

---

## Stage 1 — Project Scaffolding & Monorepo Setup

**Branch:** `main`
**Commits:** 2-3

### Tasks

- Initialize a monorepo with the following structure:

```
docuchat/
├── frontend/          # Next.js 14+ (App Router) + TypeScript
├── backend/           # Python FastAPI
├── docker-compose.yml # Local dev orchestration
├── .github/
│   └── workflows/     # CI placeholder
├── .gitignore
├── LICENSE            # MIT
└── README.md
```

- **Frontend (`frontend/`):**
  - Scaffold with `npx create-next-app@latest --typescript --tailwind --app --src-dir`
  - Install dependencies: `tailwindcss`, `shadcn/ui`, `lucide-react`, `axios`, `react-query` (TanStack Query v5)
  - Configure ESLint + Prettier with consistent rules
  - Create a minimal landing page at `/` with the project name, tagline ("Chat with your documents"), and a "Get Started" button
  - Set up a global layout with a sidebar placeholder and main content area

- **Backend (`backend/`):**
  - Create Python project with `pyproject.toml` (use Poetry or pip with requirements.txt)
  - Dependencies: `fastapi`, `uvicorn`, `python-multipart`, `pydantic`, `python-dotenv`, `ruff`, `pytest`, `httpx`
  - Create the FastAPI app entry point (`main.py`) with a health check endpoint: `GET /api/health` → `{ "status": "ok", "version": "0.1.0" }`
  - Configure Ruff for linting
  - Add CORS middleware configured for the frontend origin

- **Docker:**
  - `docker-compose.yml` with services for `frontend` (Node 20) and `backend` (Python 3.11+)
  - Both services should hot-reload in dev mode

- **Config:**
  - `.env.example` with clearly commented placeholders for: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `CHROMA_HOST`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`
  - `.gitignore` covering Node, Python, .env, __pycache__, .next, etc.

### Commit Messages
```
chore: initialize monorepo with frontend and backend scaffolding
feat: add health check endpoint and landing page with project layout
chore: add docker-compose for local development
```

---

## Stage 2 — Document Upload System

**Branch:** `feat/document-upload`
**Commits:** 3-4

### Tasks

- **Backend — Upload API:**
  - Create `POST /api/documents/upload` endpoint
  - Accept PDF and DOCX files (validate MIME types: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
  - Enforce file size limit: 20MB max
  - Store uploaded files locally in a `./uploads/` directory for now (S3 comes in Stage 8)
  - Return a document record: `{ id: uuid, filename, file_type, size_bytes, status: "uploaded", created_at }`
  - Create `GET /api/documents` to list all uploaded documents
  - Create `DELETE /api/documents/{id}` to remove a document and its associated data
  - Store document metadata in a lightweight SQLite database using SQLAlchemy (async)
  - Add Alembic for database migrations from day one

- **Backend — Text Extraction:**
  - Install `PyPDF2` (or `pypdf`) and `python-docx`
  - Create a `services/extractor.py` module that:
    - Extracts text from PDFs (page by page, preserving page numbers)
    - Extracts text from DOCX (paragraph by paragraph)
    - Returns structured output: `list[{ page_number: int, content: str }]`
  - After upload, automatically trigger extraction and update document status to `"extracted"`

- **Frontend — Upload UI:**
  - Create `/documents` page with a drag-and-drop upload zone (use native HTML5 drag events or a lightweight library)
  - Show upload progress bar
  - Display uploaded documents in a clean list/card view with: filename, file type icon, size, upload date, processing status badge
  - Add a delete button per document with confirmation modal
  - Wire everything to the backend API using TanStack Query with proper loading/error/empty states

- **Tests:**
  - Backend: Test upload with valid PDF, valid DOCX, invalid file type, oversized file
  - Backend: Test text extraction for a sample PDF and DOCX
  - Frontend: Component test for upload zone and document list

### Commit Messages
```
feat: add document upload API with file validation and SQLite storage
feat: implement PDF and DOCX text extraction service
feat: add drag-and-drop upload UI with document list view
test: add upload and extraction tests
```

---

## Stage 3 — Document Chunking & Embedding Pipeline

**Branch:** `feat/embedding-pipeline`
**Commits:** 3-4

### Tasks

- **Backend — Chunking (`services/chunker.py`):**
  - Implement recursive character text splitting with:
    - `chunk_size=1000` tokens (configurable)
    - `chunk_overlap=200` tokens (configurable)
  - Each chunk must carry metadata: `{ document_id, chunk_index, page_number, content, token_count }`
  - Install `tiktoken` for accurate token counting (use `cl100k_base` encoding)
  - Store chunks in the SQLite database linked to their parent document

- **Backend — Embedding (`services/embedder.py`):**
  - Support two embedding providers (configurable via env var `EMBEDDING_PROVIDER`):
    - OpenAI: `text-embedding-3-small` (1536 dimensions)
    - Anthropic: Use Voyage AI embeddings or fall back to OpenAI
  - Implement with a clean provider interface/abstract class so adding providers is easy
  - Process chunks in batches of 100 to respect rate limits
  - Add retry logic with exponential backoff for API failures

- **Backend — Vector Store (`services/vector_store.py`):**
  - Use ChromaDB as the default vector store (local mode for development, persistent storage)
  - Create a collection per document (or a single collection with document_id filtering — justify your choice in a code comment)
  - Store embeddings with full metadata (document_id, chunk_index, page_number, original text)
  - Implement `search(query: str, document_ids: list[str], top_k: int = 5)` method that returns ranked chunks with similarity scores

- **Backend — Processing Pipeline:**
  - After text extraction, automatically trigger chunking → embedding → vector storage
  - Update document status through: `"uploaded"` → `"extracting"` → `"chunking"` → `"embedding"` → `"ready"` (or `"failed"` with error message)
  - Create `GET /api/documents/{id}/status` endpoint for polling

- **Frontend — Processing Status:**
  - Show real-time processing status on each document card (polling every 2 seconds while processing)
  - Add a processing progress indicator (step-based: Extracting → Chunking → Embedding → Ready)
  - Only enable chat for documents with `"ready"` status

- **Tests:**
  - Chunker: Verify chunk sizes, overlap, metadata accuracy
  - Embedder: Mock the API, verify batching and retry logic
  - Vector store: Test insert and search with known embeddings
  - Integration: Upload → extract → chunk → embed → verify searchable

### Commit Messages
```
feat: implement recursive text chunking with token counting
feat: add embedding service with OpenAI provider and batch processing
feat: integrate ChromaDB vector store with similarity search
feat: add processing pipeline with status tracking and frontend polling
test: add chunking, embedding, and vector store tests
```

---

## Stage 4 — Chat Interface & RAG Core

**Branch:** `feat/chat-rag`
**Commits:** 4-5

### Tasks

- **Backend — Chat API:**
  - Create `POST /api/chat` endpoint accepting: `{ message: str, document_ids: list[str], conversation_id?: str }`
  - Implement the RAG pipeline:
    1. Embed the user's query
    2. Retrieve top-k relevant chunks from the vector store (filtered by selected document_ids)
    3. Construct a prompt that includes the retrieved chunks as context with clear source markers
    4. Send to LLM and stream the response back
  - Support two LLM providers (configurable via `LLM_PROVIDER` env var):
    - OpenAI: `gpt-4o` or `gpt-4o-mini`
    - Anthropic: `claude-sonnet-4-20250514`
  - **Streaming:** Use Server-Sent Events (SSE) for streaming responses token-by-token
  - System prompt must instruct the LLM to:
    - Answer based only on the provided context
    - Cite sources using `[Source: filename, Page X]` format inline
    - Say "I don't have enough information in the provided documents to answer this" when context is insufficient
  - Store conversation history in SQLite: conversations table and messages table

- **Backend — Conversation Management:**
  - `GET /api/conversations` — list all conversations
  - `GET /api/conversations/{id}` — get conversation with full message history
  - `DELETE /api/conversations/{id}` — delete a conversation
  - Each message stored with: role (user/assistant), content, source_chunks (JSON array of chunk references), timestamp

- **Frontend — Chat UI:**
  - Create `/chat` page with a split layout:
    - Left sidebar: document selector (checkboxes to pick which docs to query) + conversation history list
    - Main area: chat messages + input
  - Message bubbles: user messages right-aligned, assistant messages left-aligned
  - **Streaming display:** Show assistant responses appearing token-by-token as SSE events arrive
  - **Source citations:** Parse `[Source: filename, Page X]` references in assistant messages and render them as clickable chips/badges
  - Auto-scroll to bottom on new messages
  - Show a typing indicator while the assistant is generating
  - Input: multiline text area with send button and Ctrl+Enter shortcut
  - Empty state: helpful prompt suggestions when no messages exist ("Try asking: What are the key findings in this document?")

- **Tests:**
  - RAG pipeline: Mock LLM, verify context construction and citation format
  - Chat API: Test conversation creation, message storage, streaming
  - Frontend: Component tests for chat message rendering, source citation parsing

### Commit Messages
```
feat: implement RAG pipeline with context retrieval and LLM integration
feat: add streaming chat API with server-sent events
feat: add conversation management endpoints
feat: build chat UI with streaming responses and source citations
test: add RAG pipeline and chat API tests
```

---

## Stage 5 — Source Citation Viewer & Document Preview

**Branch:** `feat/source-viewer`
**Commits:** 2-3

### Tasks

- **Backend — Chunk Retrieval:**
  - Create `GET /api/documents/{id}/chunks?page={page_number}` to retrieve chunks for a specific page
  - Create `GET /api/chunks/{chunk_id}` to retrieve a single chunk with full context (surrounding chunks)

- **Frontend — Source Panel:**
  - When a user clicks a source citation chip in a chat message, open a right-side panel showing:
    - The document name and page number
    - The exact chunk text that was used as context, highlighted
    - Surrounding text for context (previous and next chunks)
    - A "View Full Page" button
  - Implement smooth panel slide-in animation
  - The panel should not disrupt the chat — it overlays or shares space via a resizable split view

- **Frontend — Document Preview:**
  - Create `/documents/{id}` page showing:
    - Document metadata (name, size, pages, upload date, chunk count)
    - Full extracted text organized by page
    - Search within the document's extracted text (client-side filter)

- **Tests:**
  - Verify citation click opens correct chunk
  - Verify surrounding context loads correctly

### Commit Messages
```
feat: add source citation panel with chunk context display
feat: add document preview page with text search
test: add source viewer component tests
```

---

## Stage 6 — Authentication & Multi-User Support

**Branch:** `feat/auth`
**Commits:** 3-4

### Tasks

- **Backend — Auth:**
  - Implement JWT-based authentication with refresh tokens
  - Endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh`, `POST /api/auth/logout`
  - Password hashing with `bcrypt`
  - All document, conversation, and chat endpoints must be scoped to the authenticated user
  - Add a `users` table: id, email, hashed_password, name, created_at
  - Add `user_id` foreign key to documents and conversations tables (migration)
  - Rate limiting: 20 chat messages per minute per user (use an in-memory counter or Redis if you prefer)

- **Frontend — Auth UI:**
  - Login page at `/login` with email/password form
  - Registration page at `/register`
  - Protected route wrapper — redirect to `/login` if not authenticated
  - Store JWT in httpOnly cookie (preferred) or secure in-memory storage (NOT localStorage)
  - Add user avatar/name in the sidebar header with a logout dropdown

- **Tests:**
  - Auth flow: register, login, access protected route, refresh token, logout
  - Authorization: verify user A cannot access user B's documents
  - Rate limiting: verify 429 response after exceeding limit

### Commit Messages
```
feat: implement JWT authentication with registration and login
feat: add user scoping to documents and conversations
feat: build auth UI with protected routes
test: add authentication and authorization tests
```

---

## Stage 7 — Performance, Polish & Error Handling

**Branch:** `feat/polish`
**Commits:** 3-4

### Tasks

- **Backend Optimizations:**
  - Add async processing queue for document processing (use `asyncio` task queue or Celery with Redis)
  - Implement caching for embeddings of repeated queries (simple LRU cache)
  - Add request/response logging middleware with correlation IDs
  - Structured JSON logging (use `structlog` or `python-json-logger`)

- **Frontend Polish:**
  - Dark mode / light mode toggle (persist preference)
  - Responsive design — fully functional on mobile viewports
  - Skeleton loading states for document list and chat history
  - Toast notifications for success/error events (use shadcn/ui toast)
  - Keyboard shortcuts: `/` to focus search, `Esc` to close panels, `N` for new conversation
  - Empty states with illustrations or helpful copy for: no documents, no conversations, no search results
  - Animated page transitions

- **Error Handling:**
  - Global error boundary in Next.js
  - Backend: custom exception classes, consistent error response schema: `{ error: { code, message, details? } }`
  - Frontend: display user-friendly error messages, never raw stack traces
  - Network retry logic for failed API calls (TanStack Query handles this, but configure it)

- **Tests:**
  - Error boundary rendering
  - Network failure handling
  - Mobile responsive behavior (visual regression tests optional but encouraged)

### Commit Messages
```
feat: add async document processing queue
feat: implement dark mode and responsive design
feat: add global error handling with structured logging
test: add error handling and edge case tests
```

---

## Stage 8 — AWS Deployment Infrastructure

**Branch:** `feat/aws-deployment`
**Commits:** 4-5

### Tasks

- **Infrastructure as Code (CDK or Terraform — pick one, CDK preferred for this stack):**
  - **S3:** Bucket for document storage (replace local `./uploads/`)
    - Configure lifecycle rules, encryption at rest, CORS for presigned URLs
  - **ECS Fargate:** Run the FastAPI backend as a containerized service
    - Create Dockerfile for backend (multi-stage build, non-root user)
    - Task definition with appropriate CPU/memory
    - Application Load Balancer in front of ECS
    - Auto-scaling based on CPU utilization
  - **RDS PostgreSQL (or Aurora Serverless):** Replace SQLite for production
    - Add SQLAlchemy async support for PostgreSQL (`asyncpg`)
    - Alembic migration must work against both SQLite (dev) and PostgreSQL (prod)
  - **Secrets Manager:** Store API keys and database credentials
  - **CloudFront + S3:** Host the Next.js frontend as a static export (or use Vercel/Amplify — state your choice and why)
  - **VPC:** Private subnets for ECS and RDS, public subnets for ALB

- **Backend Changes:**
  - Abstract file storage into `services/storage.py` with `LocalStorage` and `S3Storage` implementations
  - Switch storage based on `STORAGE_BACKEND` env var (`local` for dev, `s3` for prod)
  - Update document upload to use presigned URLs for direct-to-S3 upload from the frontend
  - Switch vector store to hosted ChromaDB or Pinecone for production (configurable)

- **CI/CD (`.github/workflows/`):**
  - `ci.yml`: Run linting + tests on every PR to `main`
  - `deploy.yml`: On merge to `main`, build Docker images, push to ECR, deploy to ECS
  - Environment variables managed via GitHub Secrets

- **Monitoring:**
  - CloudWatch logs from ECS tasks
  - Health check endpoint used by ALB for service health
  - Basic CloudWatch alarms for 5xx error rate and high latency

### Commit Messages
```
feat: add Dockerfiles with multi-stage builds for production
feat: implement S3 storage backend with presigned uploads
feat: add AWS CDK infrastructure stack (ECS, RDS, S3, CloudFront)
ci: add GitHub Actions for CI/CD pipeline
feat: add CloudWatch monitoring and health check alarms
```

---

## Stage 9 — API Documentation & Developer Experience

**Branch:** `feat/api-docs`
**Commits:** 2

### Tasks

- **Backend:**
  - FastAPI auto-generates OpenAPI docs — ensure all endpoints have:
    - Descriptive summary and description
    - Request/response model examples
    - Proper HTTP status codes documented (200, 201, 400, 401, 403, 404, 422, 429, 500)
  - Add a Postman collection export or OpenAPI JSON download link
  - Add `GET /api/docs` redirect to Swagger UI

- **README.md — Final Version:**
  - Project overview with a compelling description
  - Architecture diagram (create as Mermaid or ASCII art in the repo)
  - Screenshots or GIFs of key features (upload, chat with streaming, source citations)
  - Tech stack section with badges
  - Quick start guide (docker-compose up in 3 commands)
  - Environment variables reference table
  - API endpoints summary table
  - Deployment guide for AWS
  - Contributing guidelines
  - License (MIT)

### Commit Messages
```
docs: add comprehensive API documentation with examples
docs: finalize README with architecture diagram and setup guide
```

---

## Stage 10 — Demo Data & Final Touches

**Branch:** `feat/demo`
**Commits:** 2

### Tasks

- Create a `/scripts/seed.py` script that:
  - Registers a demo user (email: `demo@docuchat.dev`, password: `demo1234`)
  - Uploads 2-3 sample PDF documents (include in `/samples/` directory — use public domain documents like an RFC, a classic book excerpt, or a research paper with permissive license)
  - Processes them through the full pipeline
  - Creates a sample conversation with a few Q&A pairs

- Add a "Try Demo" button on the landing page that logs in as the demo user

- Final code quality sweep:
  - Remove all `TODO` and `FIXME` comments (or resolve them)
  - Ensure no unused imports or dead code
  - Run full test suite — everything green
  - Run linters — zero warnings

### Commit Messages
```
feat: add seed script with demo data and sample documents
chore: final code quality sweep and cleanup
```

---

## Architecture Summary

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│            Next.js 14 + TypeScript               │
│         TanStack Query + shadcn/ui               │
│              Tailwind CSS                        │
├──────────────────┬──────────────────────────────┤
│   CloudFront     │        ALB (HTTPS)            │
├──────────────────┴──────────────────────────────┤
│                                                  │
│                Backend (ECS Fargate)              │
│                 FastAPI + Python                  │
│                                                  │
│  ┌─────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Upload  │  │   RAG    │  │  Chat + SSE    │  │
│  │ Service │  │ Pipeline │  │  Streaming     │  │
│  └────┬────┘  └────┬─────┘  └───────┬────────┘  │
│       │            │                │            │
├───────┼────────────┼────────────────┼────────────┤
│       ▼            ▼                ▼            │
│  ┌────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │   S3   │  │ ChromaDB │  │  OpenAI /        │ │
│  │ Bucket │  │ /Pinecone│  │  Anthropic API   │ │
│  └────────┘  └──────────┘  └──────────────────┘ │
│       │                                          │
│  ┌────┴──────────────────────────────────┐       │
│  │    RDS PostgreSQL (prod)              │       │
│  │    SQLite (dev)                       │       │
│  └───────────────────────────────────────┘       │
└─────────────────────────────────────────────────┘
```

---

## Key Technologies

| Layer         | Technology                              |
|---------------|------------------------------------------|
| Frontend      | Next.js 14, TypeScript, Tailwind, shadcn/ui |
| Backend       | Python 3.11+, FastAPI, SQLAlchemy, Alembic |
| LLM           | OpenAI GPT-4o / Anthropic Claude (configurable) |
| Embeddings    | OpenAI text-embedding-3-small           |
| Vector Store  | ChromaDB (dev) / Pinecone (prod)        |
| Database      | SQLite (dev) / PostgreSQL (prod)        |
| File Storage  | Local (dev) / AWS S3 (prod)             |
| Deployment    | AWS ECS Fargate, CloudFront, RDS, S3    |
| CI/CD         | GitHub Actions                           |
| Containerization | Docker + docker-compose              |

---

## How to Use This Prompt with Claude Code

Open Claude Code in your terminal at the root of a new empty directory and give it one stage at a time:

```
You are building DocuChat. Here is the full build plan: [paste entire plan or reference file]

Start with Stage 1. Complete all tasks, write all tests, commit with the
specified messages, then confirm what you've done before we move to Stage 2.
```

After each stage, review the output, test it manually, then proceed:

```
Stage 1 looks good. Proceed to Stage 2.
```

If you need to iterate on a stage:

```
The upload progress bar isn't showing. Fix it within the current stage
before committing.
```

---

## Resume Talking Points This Project Enables

- Designed and built a full-stack RAG application supporting PDF/DOCX ingestion with chunking, embedding, and semantic search
- Implemented streaming chat with inline source citations using SSE and configurable LLM providers (OpenAI, Anthropic)
- Built a scalable processing pipeline: upload → extract → chunk → embed → index, with real-time status tracking
- Deployed on AWS using ECS Fargate, RDS PostgreSQL, S3, and CloudFront with CI/CD via GitHub Actions
- Achieved comprehensive test coverage across unit, integration, and API tests
