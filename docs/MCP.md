# MCP Server

Lumineer exposes a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server at `/mcp`, allowing any MCP-compatible AI client (Claude Desktop, Cursor, VS Code, etc.) to search courses, analyse skill gaps, and generate learning paths — without requiring the user to have an OpenAI API key.

---

## Overview

| Property | Value |
|----------|-------|
| Transport | Streamable HTTP |
| Endpoint (dev) | `http://localhost:8001/mcp` |
| Authentication | OAuth 2.1 + PKCE (optional in dev, required in prod) |
| Authorization Server | Keycloak 26 (Docker, `--profile mcp`) |
| Tools | 4 (see below) |

The MCP server is **co-located with the AI Processing service** — both run on port `8001`. A Starlette router mounts `/mcp` to FastMCP and `/` to Litestar:

```
:8001/       → Litestar REST API (health, search, agents/chat)
:8001/mcp    → FastMCP server (Streamable HTTP, OAuth 2.1)
```

---

## Quick Start (dev — no auth)

The MCP server starts automatically with the `app` profile. No extra configuration is needed in dev mode.

```bash
docker compose --profile app up -d
```

Add to your MCP client config:

```json
{
  "mcpServers": {
    "course-finder": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "course-finder": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

---

## MCP Tools

### `ask_course_finder`

Natural language entry point. Routes to the appropriate specialist agent (Search, Skill Gap, or Path) via the Triage Agent.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Any course-related question in natural language |

**Examples:**

```
"Find Python courses for beginners"
"What skills do I need to become a data scientist?"
"Build me a 3-month plan to learn web development"
```

**Returns:** Agent response with course recommendations, skill analysis, or a learning path depending on query intent.

---

### `search_courses_mcp`

Filter-based hybrid RAG search (semantic + keyword). Use when you want structured, reproducible results.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Search query — keyword or natural language |
| `level` | string | — | `"Beginner"` · `"Intermediate"` · `"Advanced"` |
| `organization` | string | — | Provider (e.g., `"Stanford"`, `"Google"`) |
| `min_rating` | float | — | Minimum course rating (0.0–5.0) |
| `skills` | string[] | — | Required skills (e.g., `["Python", "ML"]`) |
| `limit` | int | — | Max results (default 10, max 100) |

**Returns:** Formatted list with title, org, level, rating, enrolled count, and skills.

---

### `get_skill_gap_mcp`

Identifies which skills are needed for a target role that the user does not yet have.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_role` | string | ✅ | Career goal (e.g., `"Data Scientist"`, `"ML Engineer"`) |
| `current_skills` | string[] | — | Skills already possessed (e.g., `["Python", "SQL"]`) |
| `level` | string | — | Preferred course difficulty |
| `limit` | int | — | Max courses to analyse (default 10, max 100) |

**Returns:**

```
=== Skill Gap Analysis for: Data Scientist ===

Skills you already have (2): Python, SQL
Skills to acquire (4): Deep Learning, Machine Learning, Statistics, TensorFlow

--- Relevant Courses ---
...
```

---

### `get_learning_path_mcp`

Creates a step-by-step learning path toward a goal, grouped by difficulty level.

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal` | string | ✅ | Learning objective (e.g., `"Become a web developer"`) |
| `current_skills` | string[] | — | Skills already possessed |
| `timeframe` | string | — | Desired completion time (e.g., `"3 months"`) |
| `limit` | int | — | Max courses in path (default 15, max 100) |

**Returns:**

```
=== Learning Path Data for: Become a web developer ===
Target timeframe: 3 months
Total courses found: 12

--- Courses by Level ---
[Beginner] (5 courses)
  - HTML, CSS, and Javascript for Web Developers (Johns Hopkins, rating: 4.7)
  ...
[Intermediate] (4 courses)
  ...
```

---

## Architecture

```
MCP Client (Claude Desktop / Cursor / VS Code)
    │
    │  Streamable HTTP POST /mcp
    ▼
AI Processing Service (:8001/mcp)
    │
    ├── ask_course_finder ──► Triage Agent ──► handoff() ──► Specialist Agent
    │                                                              │
    ├── search_courses_mcp ──────────────────────────────────────►│
    │                                                     SearchCoursesUseCase
    ├── get_skill_gap_mcp ──────────────────────────────────────►│
    │                                                     + skill comparison
    └── get_learning_path_mcp ─────────────────────────────────►│
                                                         + level grouping
```

All four tools re-use the same RAG pipeline as the Web UI (Explore / Chat pages). The MCP server is a new entry point, not a new pipeline.

---

## Authentication (OAuth 2.1)

### Dev mode (default)

When `KEYCLOAK_URL` is unset, the server starts without authentication. All tools are accessible without a token.

### With Keycloak (optional in dev)

Start the `mcp` profile to launch Keycloak:

```bash
docker compose --profile app --profile mcp up -d
```

Then enable auth in `.env.local`:

```env
KEYCLOAK_URL=http://localhost:8080
MCP_REQUIRE_AUTH=true
```

And restart the AI service:

```bash
# If running directly (worktree dev flow)
cd ai && uv run python main.py

# If running via Docker
docker compose --profile app --profile mcp up -d --force-recreate ai
```

#### Keycloak dev console

| URL | `http://localhost:8080` |
|-----|------------------------|
| Admin username | `admin` |
| Admin password | `admin` |
| Realm | `lumineer` |
| Dev user | `dev@example.com` / `password` |

#### OAuth 2.1 flow

```
MCP Client
    │ 1. Connect to /mcp
    ▼
MCP Server ──► 401 + Protected Resource Metadata
    │            (/.well-known/oauth-protected-resource/mcp)
    │
    │ 2. Open browser
    ▼
Keycloak (:8080)
    │ User logs in + clicks "Allow"
    │ PKCE code challenge (S256)
    ▼
MCP Client receives JWT access token
    │
    │ 3. Bearer <token> on every request
    ▼
MCP Server validates token against Keycloak JWKS
    │ audience: "mcp-server"  issuer: keycloak.../realms/lumineer
    ▼
Tools available
```

#### Token lifetimes

| Token | Lifetime |
|-------|---------|
| Access token | 30 minutes |
| Refresh token | 30 days |

### Production

In production, set the following environment variables:

```env
KEYCLOAK_URL=https://your-keycloak-url
KEYCLOAK_REALM=lumineer
MCP_REQUIRE_AUTH=true
MCP_RESOURCE_SERVER_URL=https://your-ai-service.run.app/mcp
```

`MCP_RESOURCE_SERVER_URL` is required when `MCP_REQUIRE_AUTH=true` in `APP_ENV=prod` — the app will refuse to start without it.

---

## Protected Resource Metadata

FastMCP automatically exposes the RFC 9728 metadata endpoint when `AuthSettings` is configured:

```
GET /.well-known/oauth-protected-resource/mcp
```

```json
{
  "resource": "https://your-ai-service.run.app/mcp",
  "authorization_servers": ["https://your-keycloak-url/realms/lumineer"],
  "bearer_methods_supported": ["header"],
  "resource_documentation": "https://github.com/nakamu12/lumineer"
}
```

MCP clients use this endpoint to auto-discover the Authorization Server and initiate the OAuth flow.

---

## Implementation Notes

- Tool functions are plain `async def` (not `@mcp.tool` decorators) so they can be unit-tested in isolation without an MCP runtime.
- `mcp.add_tool(fn, description=...)` registers them on the `FastMCP` instance.
- The `KeycloakTokenVerifier` implements the `TokenVerifier` protocol from the MCP SDK — it validates JWTs against Keycloak's JWKS endpoint and returns an `AccessToken` on success or `None` on failure.
- JWT audience is set to `"mcp-server"` to prevent tokens issued for other Keycloak clients from being accepted.

See [`ai/app/interfaces/mcp/server.py`](../ai/app/interfaces/mcp/server.py) and [`ai/app/interfaces/mcp/auth.py`](../ai/app/interfaces/mcp/auth.py) for the implementation.
