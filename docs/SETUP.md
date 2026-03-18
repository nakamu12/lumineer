# Local Development Setup

This guide walks you through setting up Lumineer on your local machine from scratch.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker + Docker Compose | latest | https://docs.docker.com/get-docker/ |
| Bun | ≥ 1.1 | `curl -fsSL https://bun.sh/install \| bash` |
| uv (Python package manager) | ≥ 0.4 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Git | any | https://git-scm.com |

You also need an **OpenAI API key** from https://platform.openai.com/api-keys.

---

## Step 1: Clone the repository

```bash
git clone https://github.com/nakamu12/lumineer.git
cd lumineer
```

---

## Step 2: Create `.env.local`

This file holds secrets for local development. It is `.gitignore`d and never committed.

```bash
cp .env.example .env.local
```

Open `.env.local` and fill in the required values:

```env
# Required
OPENAI_API_KEY=sk-...

# Pre-filled with Docker Compose defaults — change only if you use different ports
DATABASE_URL=postgres://lumineer:lumineer@localhost:5432/lumineer
QDRANT_URL=http://localhost:6333
```

---

## Step 3: Start infrastructure

PostgreSQL and Qdrant run as Docker containers. The app services are started separately (see below).

```bash
docker compose up -d
```

Verify both are healthy:

```bash
docker compose ps
# postgres  running (healthy)
# qdrant    running
```

---

## Step 4: Install dependencies

```bash
# Backend + Gateway + Frontend
cd backend  && bun install && cd ..
cd gateway  && bun install && cd ..
cd frontend && bun install && cd ..

# AI Processing
cd ai && uv sync && cd ..
```

---

## Step 5: Run database migrations

```bash
cd backend
bun run db:migrate
cd ..
```

---

## Step 6: Seed the vector database (first time only)

This downloads and preprocesses the Coursera dataset (~6,645 courses), generates embeddings, and upserts them into Qdrant. It takes a few minutes and costs ~$0.26 in OpenAI embedding fees.

```bash
cd ai
uv run python scripts/seed_data.py
cd ..
```

> **Skip this step** if Qdrant already contains the `courses` collection (e.g. restoring from a snapshot).

---

## Step 7: Start all services

Open four terminal windows:

```bash
# Terminal 1 — Backend (port 3001)
cd backend && bun dev

# Terminal 2 — AI Processing (port 8001)
cd ai && uv run python main.py

# Terminal 3 — Gateway (port 3000)
cd gateway && BACKEND_URL=http://localhost:3001 bun dev

# Terminal 4 — Frontend (port 5173)
cd frontend && bun dev
```

Open **http://localhost:5173** in your browser.

### Port summary

| Service | Port |
|---------|------|
| Frontend (Vite) | 5173 |
| Gateway (Hono) | 3000 |
| Backend (Hono) | 3001 |
| AI Processing (Litestar) | 8001 |
| PostgreSQL | 5432 |
| Qdrant HTTP | 6333 |
| Qdrant gRPC | 6334 |

---

## Alternative: Full Docker setup

If you prefer running everything in containers:

```bash
docker compose --profile app up -d
```

This starts all services including frontend, gateway, backend, and AI processing. Hot-reload is not available in this mode.

---

## Optional: MCP Server (stretch goal)

The MCP server at `http://localhost:8001/mcp` starts automatically with the `app` profile. No extra steps are required to use it without authentication.

```bash
# MCP server is already running — add to Claude Desktop config:
# ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "course-finder": { "url": "http://localhost:8001/mcp" }
  }
}
```

### With OAuth 2.1 authentication (Keycloak)

Start the `mcp` profile to launch Keycloak as the Authorization Server:

```bash
docker compose --profile app --profile mcp up -d
```

| Service | URL | Credentials |
|---------|-----|-------------|
| Keycloak Admin Console | http://localhost:8080 | `admin` / `admin` |
| Dev user | — | `dev@example.com` / `password` |

Then enable auth in `.env.local` and restart the AI service:

```env
KEYCLOAK_URL=http://localhost:8080
MCP_REQUIRE_AUTH=true
```

```bash
# Restart AI Processing to pick up new env vars
docker compose --profile app --profile mcp up -d --force-recreate ai
```

MCP clients will now be redirected to Keycloak for login on first connection.

> See [docs/MCP.md](MCP.md) for full MCP documentation.

---

## Optional: Observability stack

```bash
docker compose --profile observability up -d
```

| Tool | URL | Description |
|------|-----|-------------|
| Grafana | http://localhost:3002 | Metrics dashboard |
| Prometheus | http://localhost:9090 | Metrics scraping |
| Langfuse | http://localhost:3003 | LLM tracing |

---

## Verify the setup

### Check the API

```bash
# Health check (no auth required)
curl http://localhost:3000/health

# Search courses
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning for beginners"}'
```

### Run tests

```bash
cd backend  && bun test
cd frontend && bun test
cd ai       && pytest
```

---

## Troubleshooting

### `OPENAI_API_KEY` not found

Ensure `.env.local` is in the project root (not inside a service directory). The backend reads `../.env.local` relative to `backend/`.

### Qdrant connection refused

Make sure Docker is running and `docker compose up -d` completed successfully:

```bash
curl http://localhost:6333/health
# {"title":"qdrant - health","status":"ok"}
```

### PostgreSQL migration fails

Check the database is reachable:

```bash
docker compose ps postgres
# Should be "running (healthy)"
```

If not, wait a few seconds for the health check to pass and retry.

### AI Processing crashes on startup

The `OPENAI_API_KEY` must be set. Litestar validates it at startup via Pydantic Settings and will raise a `ValidationError` if missing.

### Port already in use

You can override any port via environment variables:

```bash
GATEWAY_PORT=3010 BACKEND_PORT=3011 docker compose up -d
```

Or just kill the conflicting process:

```bash
lsof -i :3000 | grep LISTEN
kill -9 <PID>
```
