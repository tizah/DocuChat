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

**Stage 3 complete:** Document chunking and embedding pipeline.

- Full processing pipeline: upload → extract → chunk → embed → index
- Recursive text chunking with tiktoken token counting (configurable size/overlap)
- OpenAI embedding provider with batch processing and exponential backoff retry
- ChromaDB vector store with cosine similarity search and document filtering
- Real-time processing status tracking with step-based progress UI
- 33 passing backend tests covering chunking, embedding, vector store, and CRUD

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
