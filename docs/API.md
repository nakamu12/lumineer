# API Reference

All requests go through the **Gateway** at port `3000`. The gateway proxies `/api/*` to the Backend service.

Interactive Swagger UI is available at **http://localhost:3001/api/docs** (Backend direct, dev only).

---

## Base URL

| Environment | URL |
|-------------|-----|
| Local development | `http://localhost:3000` |
| Production | `https://<gateway-cloud-run-url>` |

---

## Authentication

Protected endpoints require a JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Access tokens expire in **15 minutes**. Use the refresh endpoint to obtain a new one.

---

## Endpoints

### Auth

#### `POST /api/auth/register`

Register a new user.

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "display_name": "Alice"
}
```

**Response `201`:**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "Alice"
  },
  "access_token": "<jwt>",
  "refresh_token": "<jwt>"
}
```

**Errors:** `409` Email already registered

---

#### `POST /api/auth/login`

Log in with email and password.

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response `200`:** Same shape as register.

**Errors:** `401` Invalid credentials

---

#### `POST /api/auth/refresh`

Exchange a refresh token for a new access token.

**Request body:**

```json
{
  "refresh_token": "<jwt>"
}
```

**Response `200`:**

```json
{
  "access_token": "<jwt>"
}
```

**Errors:** `401` Invalid or expired refresh token

---

#### `GET /api/auth/me` 🔒

Get the currently authenticated user's profile.

**Response `200`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "Alice",
  "created_at": "2026-01-15T09:00:00.000Z"
}
```

---

### Courses

#### `POST /api/search`

Search Coursera courses using natural language or keywords. Supports metadata filtering.

**Request body:**

```json
{
  "query": "machine learning for beginners",
  "level": "Beginner",
  "organization": "Stanford University",
  "min_rating": 4.5,
  "skills": ["Python", "TensorFlow"],
  "limit": 10
}
```

All fields except `query` are optional.

| Field | Type | Description |
|-------|------|-------------|
| `query` | string (required) | Natural language or keyword query |
| `level` | string | `"Beginner"` · `"Intermediate"` · `"Advanced"` |
| `organization` | string | Provider name (exact match) |
| `min_rating` | number | Minimum course rating (0–5) |
| `skills` | string[] | Filter by skill tags (any match) |
| `limit` | integer | Max results (default 10, max 20) |

**Response `200`:**

```json
{
  "courses": [
    {
      "id": "a1b2c3d4",
      "title": "Machine Learning Specialization",
      "organization": "Stanford University",
      "level": "Beginner",
      "rating": 4.9,
      "enrolled": 1234567,
      "skills": ["Python", "Machine Learning", "Deep Learning"],
      "description": "Learn the fundamentals of machine learning...",
      "url": "https://www.coursera.org/specializations/machine-learning-introduction",
      "instructor": "Andrew Ng",
      "schedule": "Approximately 3 months at 10 hours/week"
    }
  ],
  "summary": "Here are the top machine learning courses for beginners..."
}
```

**Errors:** `400` Invalid request · `502` AI Processing unavailable

---

#### `GET /api/courses/{id}`

Get a single course by its Qdrant point ID.

**Response `200`:** Single course object (same shape as search results).

**Errors:** `404` Course not found

---

### AI Chat

#### `POST /api/chat` 🔒 (optional)

Send a message to the Triage Agent. Returns an **SSE stream**.

Authentication is optional — unauthenticated users can chat but history is not persisted.

**Request body:**

```json
{
  "message": "I want to become a data scientist. What courses should I take?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

`session_id` is optional. Omit to start a new session.

**Response:** `text/event-stream`

```
data: {"type":"session","session_id":"550e8400-..."}

data: {"type":"text","content":"Based on your goal, "}

data: {"type":"text","content":"I recommend starting with..."}

data: {"type":"done"}
```

| Event type | Description |
|------------|-------------|
| `session` | Session ID created or confirmed (first event if `session_id` was omitted) |
| `text` | Streamed text chunk from the agent |
| `done` | Stream complete |
| `error` | Error message |

**Errors:** `502` AI Processing unavailable

---

### Chat Sessions

#### `GET /api/chat/sessions` 🔒

List all chat sessions for the authenticated user, most recent first.

**Response `200`:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Data science learning path",
    "created_at": "2026-01-15T09:00:00.000Z",
    "updated_at": "2026-01-15T09:30:00.000Z"
  }
]
```

---

#### `POST /api/chat/sessions` 🔒

Create a new chat session.

**Request body (optional):**

```json
{
  "title": "My learning journey"
}
```

**Response `201`:** Single session object.

---

#### `GET /api/chat/sessions/{id}/messages` 🔒

List all messages in a session. Only accessible by the session owner.

**Response `200`:**

```json
[
  {
    "id": "msg-uuid",
    "session_id": "session-uuid",
    "role": "user",
    "content": "I want to learn Python",
    "created_at": "2026-01-15T09:00:00.000Z"
  },
  {
    "id": "msg-uuid-2",
    "session_id": "session-uuid",
    "role": "assistant",
    "content": "Great choice! Here are some Python courses...",
    "created_at": "2026-01-15T09:00:05.000Z"
  }
]
```

**Errors:** `401` Unauthorized · `404` Session not found

---

### Learning Paths

#### `GET /api/paths` 🔒

List all saved learning paths for the authenticated user.

**Response `200`:**

```json
[
  {
    "id": "path-uuid",
    "title": "Become a Data Scientist in 6 months",
    "goal": "Get a junior data scientist job",
    "courses": [
      {"id": "course-1", "title": "Python for Everybody", "order": 1},
      {"id": "course-2", "title": "Machine Learning Specialization", "order": 2}
    ],
    "created_at": "2026-01-15T09:00:00.000Z",
    "updated_at": "2026-01-15T09:00:00.000Z"
  }
]
```

---

#### `POST /api/paths` 🔒

Save a learning path (typically generated by the Path Agent).

**Request body:**

```json
{
  "title": "Become a Data Scientist in 6 months",
  "goal": "Get a junior data scientist job",
  "courses": [
    {"id": "course-1", "title": "Python for Everybody", "order": 1}
  ]
}
```

**Response `201`:** Single path object.

---

### Settings

#### `GET /api/settings` 🔒

Get pipeline settings for the authenticated user. Returns defaults if no settings exist yet.

**Response `200`:**

```json
{
  "id": "settings-uuid",
  "reranker_strategy": "none",
  "context_format": "json",
  "top_k": 10,
  "similarity_threshold": 0.7
}
```

---

#### `PUT /api/settings` 🔒

Update pipeline settings. All fields are optional — only provided fields are updated.

**Request body:**

```json
{
  "reranker_strategy": "heuristic",
  "context_format": "toon",
  "top_k": 20,
  "similarity_threshold": 0.6
}
```

| Field | Values | Default | Description |
|-------|--------|---------|-------------|
| `reranker_strategy` | `"none"` · `"heuristic"` · `"cross-encoder"` | `"none"` | RAG reranking strategy |
| `context_format` | `"json"` · `"toon"` | `"json"` | LLM context serialization format |
| `top_k` | 5, 10, 20 | 10 | Number of search results |
| `similarity_threshold` | 0.5–0.9 | 0.7 | Minimum similarity score cutoff |

**Response `200`:** Updated settings object.

---

---

## MCP Tools

The AI Processing service also exposes an **MCP (Model Context Protocol) server** at `http://localhost:8001/mcp`. This allows any MCP-compatible client (Claude Desktop, Cursor, VS Code) to call Lumineer tools directly.

> Full documentation: [docs/MCP.md](MCP.md)

### Endpoint

| Environment | URL |
|-------------|-----|
| Local development | `http://localhost:8001/mcp` |
| Production | `https://<ai-service-cloud-run-url>/mcp` |

### Tools

| Tool | Description |
|------|-------------|
| `ask_course_finder` | Natural language query — Triage Agent routes to the appropriate specialist |
| `search_courses_mcp` | Hybrid RAG search with optional filters (level, org, rating, skills) |
| `get_skill_gap_mcp` | Skill gap analysis for a target role |
| `get_learning_path_mcp` | Learning path generation grouped by difficulty level |

### Authentication

In dev mode (default), tools are accessible without authentication.
In prod (`MCP_REQUIRE_AUTH=true`), Bearer tokens issued by Keycloak are required (OAuth 2.1 + PKCE).

---

## Error Format

All error responses follow the same shape:

```json
{
  "error": "Email already registered",
  "status": 409
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing or invalid token) |
| 404 | Not Found |
| 409 | Conflict (e.g. duplicate email) |
| 502 | Bad Gateway (AI Processing Layer unavailable) |
