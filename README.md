# Lumineer

> **Intelligent Course Discovery System** — AI-powered course search, skill gap analysis, and learning path generation built on 6,645 Coursera courses.

Lumineer lets you find the right courses through natural language, understand your skill gaps against a target role, and generate a personalized learning roadmap — all in one place.

---

## Architecture

```
Browser
  │
  ▼
Frontend  (React + Vite, :5173)
  │  HTTP / SSE
  ▼
Gateway   (Hono, :3000)   ← sole public entry point · CORS · rate-limit · proxy
  │  proxy /api/*
  ▼
Backend   (Hono, :3001)   ← Clean Architecture · JWT auth · PostgreSQL
  │  HTTP
  ▼
AI        (Python + Litestar, :8001)   ← Agents SDK · RAG pipeline · guardrails
  │
  ├── Qdrant  (:6333)   vector search
  └── OpenAI             embeddings + LLM
```

**Dependency flow:** `Frontend → Gateway → Backend → AI Processing → Qdrant / OpenAI`

Each layer is independently deployable. The AI layer never knows about the frontend.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Bun · React 18 · Vite · Shadcn UI · Tailwind CSS |
| Gateway | Bun · Hono (TypeScript) |
| Backend | Bun · Hono · Drizzle ORM · PostgreSQL · JWT (jose) |
| AI Processing | Python 3.12 · Litestar · OpenAI Agents SDK |
| Vector DB | Qdrant (hybrid search — dense + sparse + RRF) |
| Embedding | OpenAI `text-embedding-3-large` (3072 dim) |
| LLM | OpenAI `gpt-4o-mini` |
| Observability | Langfuse · Prometheus · Grafana |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- [Bun](https://bun.sh) ≥ 1.1
- [uv](https://github.com/astral-sh/uv) ≥ 0.4
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1. Clone and configure

```bash
git clone https://github.com/nakamu12/lumineer.git
cd lumineer
echo "OPENAI_API_KEY=sk-..." > .env.local
```

### 2. Start infrastructure

```bash
docker compose up -d        # PostgreSQL + Qdrant
```

### 3. Seed the vector database (first time only)

```bash
cd ai
uv sync
uv run python scripts/seed_data.py
cd ..
```

### 4. Start all services

```bash
# Terminal 1 — Backend
cd backend && bun install && bun dev

# Terminal 2 — AI Processing
cd ai && uv run python main.py

# Terminal 3 — Gateway
cd gateway && bun install && bun dev

# Terminal 4 — Frontend
cd frontend && bun install && bun dev
```

Open **http://localhost:5173** in your browser.

> **Full Docker setup:** `docker compose --profile app up -d` starts everything at once.

---

## Services

| Service | Directory | Port | README |
|---------|-----------|------|--------|
| Frontend | `frontend/` | 5173 | [frontend/README.md](frontend/README.md) |
| Gateway | `gateway/` | 3000 | [gateway/README.md](gateway/README.md) |
| Backend | `backend/` | 3001 | [backend/README.md](backend/README.md) |
| AI Processing | `ai/` | 8001 | [ai/README.md](ai/README.md) |

---

## Key Commands

```bash
# Lint + type check
cd frontend && bun run lint && bun run typecheck
cd backend  && bun run lint && bun run typecheck
cd ai       && ruff check . && mypy .

# Tests
cd frontend && bun test
cd backend  && bun test
cd ai       && pytest

# Database migrations
cd backend && bun run db:generate && bun run db:migrate
```

---

## Pages

| Path | Auth | Description |
|------|------|-------------|
| `/` | — | Landing — value proposition + quick start |
| `/explore` | — | Course catalog — search, filter, AI summary |
| `/chat` | ✓ | AI conversation — search, skill gap, path generation |
| `/path` | ✓ | Learning path management |
| `/course/:id` | — | Course detail |
| `/settings` | ✓ | Pipeline settings (reranker, format, top-k) |

---

## Documentation

### Getting Started

| Document | Description |
|----------|-------------|
| [docs/SETUP.md](docs/SETUP.md) | Detailed local development setup |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide, branching, PR rules |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | End-user guide for all pages and features |

### Architecture & Design

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, sequence diagrams, ER diagram, ADR index |
| [docs/AGENTS.md](docs/AGENTS.md) | Agent map, tool signatures, guardrail design |
| [docs/RAG_PIPELINE.md](docs/RAG_PIPELINE.md) | Full RAG pipeline — ingestion, hybrid search, reranking, formatting |
| [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) | Qdrant payload schema, PostgreSQL tables, entity types, JWT claims |
| [docs/adr.md](docs/adr.md) | Architecture Decision Records ADR-001–013 |
| [docs/requirements.md](docs/requirements.md) | Full product requirements (Japanese) |

### API & Integration

| Document | Description |
|----------|-------------|
| [docs/API.md](docs/API.md) | REST API endpoint reference with request/response examples |

### Operations & Deployment

| Document | Description |
|----------|-------------|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Step-by-step GCP deployment guide, CI/CD pipeline, cost estimate |
| [docs/INFRA.md](docs/INFRA.md) | Terraform IaC reference — resources, variables, IAM design |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Monitoring, alerting, incident response, RAG quality monitoring |
| [SECURITY.md](SECURITY.md) | Auth design, secret management, OWASP mitigations, LLM security |

### Testing

| Document | Description |
|----------|-------------|
| [docs/TESTING.md](docs/TESTING.md) | 3-layer test strategy, Golden Dataset, DeepEval metrics, CI/CD gates |

---

## Production Deployment

Production runs on **GCP Cloud Run** + **Firebase Hosting** + **Qdrant Cloud** at ~$6/month.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full deployment guide and [docs/INFRA.md](docs/INFRA.md) for Terraform reference.

---

## License

MIT
