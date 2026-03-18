# AI Processing

The **AI Processing Service** for Lumineer. Built with Python 3.12 + Litestar following Clean Architecture.

Handles: multi-agent orchestration (OpenAI Agents SDK) · RAG pipeline · 5-layer guardrails · observability.

Internal only — called exclusively by the Backend service, never exposed to the internet.

---

## Architecture

```
interfaces/api/ → usecases/ → ports/ ← infrastructure/
                      ↕
                   domain/
           (entities, ports — no external deps)
```

Agent flow:

```
User message → Triage Agent
                    │ handoff()
          ┌─────────┼──────────┐
          ▼         ▼          ▼
    Search Agent  Skill Gap  Path Agent
    (search_courses) (analyze_skill_gap) (generate_learning_path)
```

---

## Directory structure

```
ai/
├── app/
│   ├── agents/                    # Agent definitions (instructions + handoffs)
│   │   ├── triage_agent.py
│   │   ├── search_agent.py
│   │   ├── skill_gap_agent.py
│   │   └── path_agent.py
│   ├── tools/                     # @function_tool definitions
│   │   ├── search_courses.py
│   │   ├── analyze_skill_gap.py
│   │   └── generate_learning_path.py
│   ├── prompts/                   # Markdown prompt templates (never hardcoded)
│   │   ├── triage.md
│   │   ├── search.md
│   │   ├── skill_gap.md
│   │   └── path.md
│   ├── guardrails/                # 5-layer defense
│   │   ├── input/                 # injection_detector, toxicity_filter, offtopic_detector
│   │   └── output/                # hallucination_checker
│   ├── domain/
│   │   ├── entities/              # Course, SkillGap, LearningPath
│   │   └── ports/                 # VectorStorePort, EmbeddingPort
│   ├── infrastructure/
│   │   ├── vectordb/              # Qdrant adapters (search + upsert)
│   │   ├── embeddings/            # OpenAI embedding adapter
│   │   ├── formatters/            # JsonFormatter, ToonFormatter
│   │   ├── reranking/             # NoReranker, HeuristicReranker, CrossEncoderReranker
│   │   └── ingestion/             # CSV loader, LLM preprocessor, chunker
│   ├── interfaces/api/            # Litestar routes
│   ├── observability/             # Langfuse tracer, Prometheus metrics
│   └── config/
│       ├── settings.py            # Pydantic Settings
│       └── container.py           # Dependency injection
├── data/
│   ├── raw/                       # coursera.parquet (source data)
│   └── processed/                 # preprocessed.jsonl (LLM output)
├── evals/
│   └── datasets/                  # Golden Dataset (JSON)
├── scripts/
│   ├── seed_data.py               # One-time ingestion pipeline
│   └── run_evals.py               # RAG evaluation runner
├── tests/
├── main.py                        # Server entry point
└── pyproject.toml
```

---

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Triage Agent** | Classify intent, route to specialist | none |
| **Search Agent** | Course search with metadata filtering | `search_courses` |
| **Skill Gap Agent** | Analyze skill gaps against a target role | `analyze_skill_gap` |
| **Path Agent** | Generate ordered learning roadmap | `generate_learning_path` |

Agents are defined in `app/agents/`. Instructions are loaded from `app/prompts/*.md` at startup — never hardcoded.

---

## RAG Pipeline

```
Query → metadata filter → hybrid search (dense + sparse) → RRF fusion
     → reranking (Strategy) → result selection → formatter → agent context
```

| Step | Implementation |
|------|---------------|
| Embedding | `text-embedding-3-large` (3072 dim) |
| Dense search | Qdrant vector similarity |
| Sparse search | Qdrant sparse vectors (BM25-equivalent) |
| Score fusion | RRF (Reciprocal Rank Fusion) |
| Reranking | Strategy pattern: `none` · `heuristic` · `cross-encoder` |
| Formatting | Strategy pattern: `json` · `toon` |

---

## Guardrails (5-layer defense)

| Layer | Component | Method |
|-------|-----------|--------|
| L1 Input | Injection detector, toxicity filter, off-topic detector | `@input_guardrail` + LLM judge |
| L4 Output | Hallucination checker (DB lookup + LLM verifier) | `@output_guardrail` |

Guardrails are applied declaratively on each agent. Multiple guardrails run in parallel to minimize latency.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `dev` | `dev` or `prod` |
| `OPENAI_API_KEY` | — | **Required** |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant endpoint |
| `QDRANT_API_KEY` | `None` | Required in prod |
| `QDRANT_COLLECTION` | `courses` | Collection name |
| `EMBEDDING_MODEL` | `text-embedding-3-large` | Embedding model |
| `LLM_MODEL` | `gpt-4o-mini` | Chat model |
| `AGENT_MODEL` | `gpt-4o-mini` | Agent model |
| `RERANKER_STRATEGY` | `none` | `none` · `heuristic` · `cross-encoder` |
| `CONTEXT_FORMAT` | `json` | `json` · `toon` |
| `TOP_K` | `10` | Default search result count |
| `SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity cutoff |

In prod, `QDRANT_API_KEY` is required (validated at startup by Pydantic).

---

## Development

```bash
# Install dependencies
uv sync

# Start server with hot-reload (reads ../.env.local)
uv run python main.py

# Lint + format
ruff check .
ruff format .

# Type check
mypy .

# Tests
pytest
pytest -v tests/test_search_agent.py  # single file
pytest --tb=short                     # shorter tracebacks
```

---

## Data ingestion (first time only)

```bash
# Full pipeline: CSV → LLM preprocessing → embedding → Qdrant upsert
uv run python scripts/seed_data.py

# Estimated cost: ~$1.36 (LLM preprocessing ~$1.10 + embedding ~$0.26)
# Estimated time: 15–30 minutes
```

The raw data file must be at `../data/coursera.parquet` relative to the `ai/` directory.

---

## RAG Evaluation

```bash
# Run DeepEval benchmarks against the Golden Dataset
uv run python scripts/run_evals.py

# Output: Hit Rate@10, Hallucination rate, Faithfulness score
```

Golden Dataset lives in `evals/datasets/`. See [docs/requirements.md § 10](../docs/requirements.md) for evaluation strategy details.

---

## Testing

```bash
pytest                         # run all tests
pytest -v                      # verbose output
pytest tests/test_formatters.py  # single module
```

Tests use pytest with `pytest-asyncio` for async route handlers. External dependencies (Qdrant, OpenAI) are mocked via dependency injection — no real API calls in unit tests.
