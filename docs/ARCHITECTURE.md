# System Architecture

## 1. System Architecture Diagram

> **Source file:** [`docs/diagrams/system-architecture.drawio`](diagrams/system-architecture.drawio)
>
> Open with [draw.io desktop app](https://github.com/jgraph/drawio-desktop/releases) or the [VS Code extension](https://marketplace.visualstudio.com/items?itemName=hediet.vscode-drawio).

The diagram covers all 4 layers (Frontend → Gateway → Backend → AI Processing), external services (Qdrant Cloud, OpenAI API), observability stack, security boundaries, and production cost breakdown.

**Layer summary:**

| Layer | Tech | Port | Deployment |
|-------|------|------|-----------|
| Frontend | React + Vite + Shadcn UI | 5173 | Firebase Hosting (CDN) |
| Gateway | Bun + Hono | 3000 | Cloud Run (public) |
| Backend | Bun + Hono + Drizzle | 3001 | Cloud Run (internal) |
| AI Processing | Python + Litestar + Agents SDK | 8001 | Cloud Run (internal) |
| PostgreSQL | PostgreSQL 16 | 5432 | Cloud SQL |
| Qdrant | Vector DB | 6333 | Qdrant Cloud (1 GB free) |

**Dependency flow:** `Frontend → Gateway → Backend → AI Processing → Qdrant / OpenAI`

---

## 2. Sequence Diagrams

### 3-1. User Registration

```mermaid
sequenceDiagram
  autonumber
  actor Browser
  participant GW as Gateway
  participant BE as Backend
  participant DB as PostgreSQL

  Browser->>GW: POST /api/auth/register<br/>{email, password, display_name}
  GW->>BE: proxy
  BE->>BE: Zod validation
  BE->>BE: bcrypt hash (cost 12)
  BE->>DB: INSERT INTO users
  DB-->>BE: user row
  BE->>BE: issue Access Token (15m) + Refresh Token (7d) via jose
  BE-->>GW: 201 {user, access_token, refresh_token}
  GW-->>Browser: 201
```

### 3-2. JWT-Authenticated Request

```mermaid
sequenceDiagram
  autonumber
  actor Browser
  participant GW as Gateway
  participant BE as Backend
  participant DB as PostgreSQL

  Browser->>GW: GET /api/settings<br/>Authorization: Bearer <token>
  GW->>BE: proxy with header
  BE->>BE: auth middleware: jose.jwtVerify()
  alt token invalid / expired
    BE-->>GW: 401 Unauthorized
    GW-->>Browser: 401
  else token valid
    BE->>BE: inject userId into context
    BE->>DB: SELECT user_settings WHERE user_id = ?
    DB-->>BE: settings row (or default)
    BE-->>GW: 200 {settings}
    GW-->>Browser: 200
  end
```

### 3-3. AI Course Search (Explore page)

```mermaid
sequenceDiagram
  autonumber
  actor Browser
  participant GW as Gateway
  participant BE as Backend
  participant AI as AI Processing
  participant QD as Qdrant
  participant OAI as OpenAI

  Browser->>GW: POST /api/search {query, filters}
  GW->>BE: proxy
  BE->>AI: POST /agents/run {query, filters, format, reranker}
  AI->>AI: Triage Agent: classify intent
  AI->>AI: handoff → Search Agent
  AI->>OAI: embed(query) text-embedding-3-large
  OAI-->>AI: vector[3072]
  AI->>QD: hybrid_search(dense, sparse, filter, top_k=20)
  QD-->>AI: ranked results (RRF)
  AI->>AI: Reranker.rerank() [none|heuristic|cross-encoder]
  AI->>AI: ResultSelector (top_k, threshold)
  AI->>AI: Formatter.format() [json|toon]
  AI->>OAI: chat.completions (Search Agent + context)
  OAI-->>AI: answer text
  AI-->>BE: {courses, summary}
  BE-->>GW: 200
  GW-->>Browser: 200
```

### 3-4. Chat with SSE Streaming

```mermaid
sequenceDiagram
  autonumber
  actor Browser
  participant GW as Gateway
  participant BE as Backend
  participant AI as AI Processing
  participant OAI as OpenAI
  participant DB as PostgreSQL

  Browser->>GW: POST /api/chat {message, session_id}<br/>Authorization: Bearer <token>
  GW->>BE: proxy
  BE->>BE: verify JWT → userId
  BE->>AI: stream request
  AI->>AI: Triage Agent evaluates intent
  AI->>AI: handoff → [Search|SkillGap|Path] Agent
  loop SSE stream
    AI->>OAI: token generation
    OAI-->>AI: token chunk
    AI-->>BE: data: {"type":"text","content":"..."}
    BE-->>GW: SSE chunk
    GW-->>Browser: SSE chunk
  end
  AI-->>BE: data: {"type":"done"}
  BE-->>Browser: data: {"type":"done"}
  BE->>DB: INSERT chat_messages (user + assistant)
```

### 3-5. Token Refresh

```mermaid
sequenceDiagram
  autonumber
  actor Browser
  participant GW as Gateway
  participant BE as Backend

  Browser->>GW: POST /api/auth/refresh {refresh_token}
  GW->>BE: proxy
  BE->>BE: jose.jwtVerify(refresh_token, JWT_SECRET)
  alt invalid / expired
    BE-->>GW: 401
    GW-->>Browser: 401 — re-login required
  else valid
    BE->>BE: issue new Access Token (15m)
    BE-->>GW: 200 {access_token}
    GW-->>Browser: 200
  end
```

---

## 4. RAG Pipeline Flow

```mermaid
flowchart TD
  Q["User Query"] --> MF["① Metadata Filter\n(level, org, rating, skills)"]
  MF --> HS["② Hybrid Search\nDense: text-embedding-3-large\nSparse: BM25-equivalent"]
  HS --> RRF["③ RRF Score Fusion\n(top_k = 20)"]
  RRF --> RR["④ Reranking\nnone / heuristic / cross-encoder"]
  RR --> RS["⑤ Result Selection\ntop_k filter + similarity threshold"]
  RS -->|"hits < threshold"| CRAG["Corrective RAG\nquery rewrite → retry ②"]
  CRAG --> HS
  RS --> FM["⑥ Formatter\njson / toon"]
  FM --> AGT["Search Agent\n(LLM answer generation)"]
  AGT --> OUT["Response to user"]
```

---

## 5. Agent Handoff Flow

```mermaid
flowchart TD
  UI["User Input"] --> GRD["Input Guardrails\n• injection_detector\n• toxicity_filter\n• offtopic_detector"]
  GRD -->|blocked| ERR["Error response"]
  GRD -->|passed| TA["Triage Agent\nclassify intent"]

  TA -->|course search| SA["Search Agent\nsearch_courses tool"]
  TA -->|skill analysis| SGA["Skill Gap Agent\nanalyze_skill_gap tool"]
  TA -->|learning path| PA["Path Agent\ngenerate_learning_path tool"]

  SA --> OG["Output Guardrail\nhallucination_checker"]
  SGA --> OG
  PA --> OG

  OG -->|hallucination detected| REGEN["Block / Regenerate"]
  OG -->|passed| RES["Final Response"]
```

---

## 6. Clean Architecture — Dependency Rule

```mermaid
graph LR
  subgraph Backend["Backend / AI Processing"]
    direction TB
    IF["interfaces/\nHono routes\nLitestar routes"]
    UC["usecases/\nbusiness logic"]
    PO["ports/\nabstract interfaces"]
    IN["infrastructure/\nDrizzle · Qdrant\nOpenAI · bcrypt"]
  end

  IF -->|calls| UC
  UC -->|depends on| PO
  IN -->|implements| PO

  style PO fill:#f0f4ff,stroke:#4f6ef7
  style UC fill:#f0fff4,stroke:#22c55e
  style IN fill:#fff7ed,stroke:#f97316
  style IF fill:#fdf4ff,stroke:#a855f7
```

**Rule:** arrows point inward only. `infrastructure/` depends on `ports/`, never vice versa. Swapping Qdrant for another vector DB means touching only `infrastructure/vectordb/`.

---

## 7. PostgreSQL ER Diagram

```mermaid
erDiagram
  users {
    uuid id PK
    varchar email UK
    varchar password_hash
    varchar display_name
    timestamptz created_at
    timestamptz updated_at
  }

  chat_sessions {
    uuid id PK
    uuid user_id FK
    varchar title
    timestamptz created_at
    timestamptz updated_at
  }

  chat_messages {
    uuid id PK
    uuid session_id FK
    varchar role
    text content
    timestamptz created_at
  }

  learning_paths {
    uuid id PK
    uuid user_id FK
    varchar title
    text goal
    jsonb courses
    timestamptz created_at
    timestamptz updated_at
  }

  user_settings {
    uuid id PK
    uuid user_id FK "UNIQUE"
    varchar reranker_strategy
    varchar context_format
    integer top_k
    real similarity_threshold
  }

  users ||--o{ chat_sessions : "has"
  chat_sessions ||--o{ chat_messages : "contains"
  users ||--o{ learning_paths : "owns"
  users ||--|| user_settings : "configures"
```

---

## 8. Production Infrastructure (GCP)

```mermaid
graph TB
  subgraph Internet
    User["Browser / MCP Client"]
  end

  subgraph GCP["Google Cloud Platform"]
    FH["Firebase Hosting\nCDN — React SPA"]
    subgraph CloudRun["Cloud Run"]
      GWR["lumineer-api\n(Gateway)\npublic HTTPS"]
      BER["lumineer-backend\n(Backend)\ninternal only"]
      AIR["lumineer-ai\n(AI Processing)\ninternal only"]
    end
    CS["Cloud SQL\nPostgreSQL 16"]
    SM["Secret Manager\nAPI keys"]
  end

  subgraph External["External Services"]
    QDC["Qdrant Cloud\n1GB free tier"]
    OAI["OpenAI API"]
  end

  User -->|HTTPS| FH
  User -->|HTTPS| GWR
  GWR -->|Cloud Run invoke| BER
  BER -->|Cloud Run invoke| AIR
  BER -->|Cloud SQL Proxy| CS
  AIR -->|HTTPS| QDC
  AIR -->|HTTPS| OAI
  AIR -.->|reads secrets| SM
  BER -.->|reads secrets| SM
```

**Access control:**
- Gateway (`lumineer-api`): `allUsers` — public HTTPS
- Backend (`lumineer-backend`): Gateway service account only
- AI Processing (`lumineer-ai`): Backend service account only

---

## 9. Technology Decisions

Key architecture decisions are recorded in [docs/adr.md](adr.md).

| ADR | Decision |
|-----|---------|
| ADR-001 | Modular monolith + Docker Compose (not microservices) |
| ADR-002 | Clean Architecture for Backend and AI Processing |
| ADR-003 | Bun + Hono for API layer |
| ADR-004 | Python + Litestar for AI Processing |
| ADR-005 | OpenAI Agents SDK (no LangChain) |
| ADR-007 | Qdrant as vector DB (hybrid search native) |
| ADR-010 | Triage pattern — 4-agent handoff architecture |
| ADR-013 | Dedicated API Gateway layer |
