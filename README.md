# DocuChat

**Chat with your documents.** Upload PDFs and DOCX files, then ask questions and get AI-powered answers with inline source citations.

DocuChat is a full-stack RAG (Retrieval-Augmented Generation) application built with Next.js, FastAPI, and configurable LLM providers.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14+, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python 3.11+, FastAPI, SQLAlchemy, Alembic |
| Package Manager | pnpm (frontend), pip (backend) |
| Containerization | Docker + docker-compose |
| CI/CD | GitHub Actions |

## Current Status

**Stage 2 complete:** Document upload system with text extraction.

- Drag-and-drop document upload (PDF/DOCX) with progress bar
- Document list with status badges, file info, and delete with confirmation
- Backend upload API with MIME type validation and 20MB size limit
- PDF text extraction (page-by-page) and DOCX text extraction
- SQLite database with SQLAlchemy async ORM and Alembic migrations
- 14 passing backend tests covering upload, extraction, and CRUD

## Quick Start

### Prerequisites

- Node.js 20+ and pnpm
- Python 3.11+
- Docker and Docker Compose (optional)

### Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
pnpm install
pnpm dev
```

**With Docker:**

```bash
cp .env.example .env
# Fill in your API keys in .env
docker compose up
```

The frontend will be available at `http://localhost:3000` and the backend at `http://localhost:8000`.

### API Docs

Once the backend is running, visit `http://localhost:8000/api/docs` for the interactive Swagger UI.

## Project Structure

```
docuchat/
├── frontend/          # Next.js 14+ (App Router) + TypeScript
├── backend/           # Python FastAPI
├── docker-compose.yml # Local dev orchestration
├── .github/
│   └── workflows/     # CI pipeline
├── .env.example       # Environment variable template
├── .gitignore
├── LICENSE            # MIT
└── README.md
```

## License

MIT
