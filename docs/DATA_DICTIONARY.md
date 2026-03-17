# Data Dictionary

This document defines every data field in Lumineer — from the source Coursera dataset to the PostgreSQL schema and Qdrant vector payload.

---

## 1. Coursera Dataset (Source)

**File:** `data/raw/coursera.parquet` — 6,645 rows, 11.4 MB

| Column | Type | Null rate | Notes |
|--------|------|-----------|-------|
| `Title` | string | 0% | Course name |
| `Description` | string | 0% | Full marketing description. Avg 3,198 chars, max 32,804 chars |
| `Skills` | string (JSON list) | 29% | Tags like `["Python", "Machine Learning"]`. Empty for 1,954 courses |
| `Level` | string | 12% | `"Beginner"` · `"Intermediate"` · `"Advanced"` · missing (778 courses) |
| `Organization` | string | 0% | Provider name e.g. `"Stanford University"` |
| `Rating` | string | 0% | Numeric string `"4.8"` — converted to `float` at ingestion |
| `Enrolled` | string | 0% | Numeric string `"1234567"` — converted to `int` at ingestion |
| `Modules/Courses` | string | varies | Course structure summary |
| `Schedule` | string | varies | Duration e.g. `"Approximately 3 months at 10 hours/week"` |
| `URL` | string | 0% | Full Coursera URL |
| `Instructor` | string | varies | Instructor name(s) |

**Data quality issues handled at ingestion:**
- `Skills` null (29%) → GPT-4o-mini infers skills from `Description`
- `Level` format varies (`"Beginner level"`, `"Beginner"`) → normalized to canonical value
- `Rating` / `Enrolled` stored as strings → cast at ingestion

---

## 2. Qdrant Vector Payload

After ingestion, each course is stored as a Qdrant point. The payload contains the original data plus the LLM-generated `search_text`.

| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| `title` | string | — | Course title (display) |
| `description` | string | — | Original full description (LLM context) |
| `skills` | string[] | ✅ `match_any` | Skill tags — used for filtering and embedding |
| `level` | string \| null | ✅ exact match | `"Beginner"` · `"Intermediate"` · `"Advanced"` · `null` |
| `organization` | string | ✅ exact match | Provider name |
| `rating` | float | ✅ range `≥ N` | 0.0–5.0 |
| `enrolled` | int | ✅ range | Total enrolled students |
| `num_reviews` | int \| null | — | Review count |
| `modules` | string \| null | — | Module/course structure (display) |
| `schedule` | string \| null | — | Estimated duration (display) |
| `url` | string | — | Coursera URL (frontend link) |
| `instructor` | string \| null | — | Instructor name(s) (display) |
| `search_text` | string | — | **LLM-generated** normalized text used for embedding |

### Vector schema

| Vector name | Dimensions | Algorithm | Purpose |
|-------------|-----------|-----------|---------|
| `dense` | 3072 | `text-embedding-3-large` cosine | Semantic similarity search |
| `sparse` | variable | BM25-equivalent | Keyword matching |

### Filtering behavior

| Field | When filter is set | When field is null/missing |
|-------|--------------------|--------------------------|
| `level` | Returns exact matches + null (to avoid false negatives) | Included in results |
| `organization` | Exact string match | Excluded from filtered results |
| `rating` | Returns docs where `rating ≥ min_rating` | Included (all courses have rating) |
| `skills` | Returns docs where any skill matches | Excluded from filtered results |

---

## 3. CourseEntity (Python Domain Object)

Defined in `ai/app/domain/entities/course.py`. Immutable (`@dataclass(frozen=True)`).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `str` | UUID format | Qdrant point ID |
| `title` | `str` | stripped | Display name |
| `description` | `str` | stripped | Full description |
| `skills` | `list[str]` | each item stripped, empty filtered | Skill tags |
| `level` | `str \| None` | `"Beginner"` · `"Intermediate"` · `"Advanced"` · `None` | Normalized in `CourseFactory` |
| `organization` | `str` | stripped | Provider |
| `rating` | `float` | `0.0 ≤ rating ≤ 5.0` | Clamped in factory |
| `enrolled` | `int` | `≥ 0` | Total students |
| `num_reviews` | `int \| None` | `≥ 0` if present | |
| `modules` | `str \| None` | stripped if present | |
| `schedule` | `str \| None` | stripped if present | |
| `url` | `str` | stripped | Coursera URL |
| `instructor` | `str \| None` | stripped if present | |
| `search_text` | `str` | stripped | LLM-generated embedding target |

**Factory normalization (`CourseFactory._normalize_level`):**

```python
# Input variations → canonical output
"Beginner level"       → "Beginner"
"beginner"             → "Beginner"
"Intermediate level"   → "Intermediate"
""                     → None
None                   → None
"Mixed"                → None  # unrecognized → None
```

---

## 4. PostgreSQL Schema

Managed by Drizzle ORM. Schema file: `backend/src/infrastructure/db/schema.ts`.

### `users`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default random | |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt, cost factor 12 |
| `display_name` | VARCHAR(100) | NOT NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL, default NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, default NOW() | |

### `chat_sessions`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → `users.id` CASCADE DELETE | |
| `title` | VARCHAR(200) | NOT NULL, default `'New Chat'` | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

### `chat_messages`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `session_id` | UUID | FK → `chat_sessions.id` CASCADE DELETE | |
| `role` | VARCHAR(20) | NOT NULL, CHECK `IN ('user', 'assistant')` | |
| `content` | TEXT | NOT NULL | Full message text |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

### `learning_paths`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → `users.id` CASCADE DELETE | |
| `title` | VARCHAR(200) | NOT NULL | |
| `goal` | TEXT | nullable | Free-text learning goal |
| `courses` | JSONB | NOT NULL, default `'[]'` | Ordered course list — see below |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

**`courses` JSONB schema:**

```typescript
type CourseRef = {
  id: string       // Qdrant point ID
  title: string    // display name (denormalized for performance)
  order: number    // sequence position (1-based)
}

// e.g.
[
  { "id": "abc123", "title": "Python for Everybody", "order": 1 },
  { "id": "def456", "title": "Machine Learning Specialization", "order": 2 }
]
```

### `user_settings`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → `users.id` CASCADE DELETE, UNIQUE | One row per user |
| `reranker_strategy` | VARCHAR(20) | NOT NULL, default `'none'` | `'none'` · `'heuristic'` · `'cross-encoder'` |
| `context_format` | VARCHAR(10) | NOT NULL, default `'json'` | `'json'` · `'toon'` |
| `top_k` | INTEGER | NOT NULL, default `10` | |
| `similarity_threshold` | REAL | NOT NULL, default `0.7` | |

---

## 5. REST API Payloads

### Auth tokens

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT, expires in 15 minutes |
| `refresh_token` | string | JWT, expires in 7 days |

**Access token claims:**

```json
{
  "sub": "<user-uuid>",
  "type": "access",
  "iat": 1700000000,
  "exp": 1700000900
}
```

### Search request / response

See [API.md](API.md) for full request/response schemas.

---

## 6. Settings Value Reference

| Setting | Values | Default | Effect |
|---------|--------|---------|--------|
| `reranker_strategy` | `none` · `heuristic` · `cross-encoder` | `none` | Post-retrieval reranking algorithm |
| `context_format` | `json` · `toon` | `json` | LLM context serialization (TOON ≈50% fewer tokens) |
| `top_k` | `5` · `10` · `20` | `10` | Number of courses returned per search |
| `similarity_threshold` | `0.5`–`0.9` | `0.7` | Minimum cosine similarity to include a result |
