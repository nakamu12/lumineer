# Lumineer — LLM & RAG Evaluation

Lumineer の AI エージェント品質を 2 つの評価パイプラインで担保する。

## Overview

| Eval | Script | Purpose | Qdrant | Where |
|------|--------|---------|--------|-------|
| **CI Eval** | `scripts/run_evals.py` | Model drift detection (Faithfulness + Hallucination) | Not required | GitHub Actions (on PR) |
| **RAG Eval** | `scripts/run_rag_evals.py` | Search pipeline quality (Hit Rate, MRR, NDCG) | Required | Local batch |

## CI Eval — Faithfulness & Hallucination

Evaluates agent response quality using pre-defined retrieval contexts from Golden Datasets.
Runs automatically on PRs that modify LLM-related files (`ai/app/agents/**`, `ai/app/prompts/**`, etc.).

### Tier 1 Thresholds (CI/CD Gate)

| Metric | Threshold | Direction |
|--------|-----------|-----------|
| Faithfulness | >= 0.70 | Higher is better (1.0 = perfectly faithful) |
| Hallucination | <= 0.50 | Lower is better (0.0 = no hallucination) |

### Run Locally

```bash
cd ai

# All categories (search, skill_gap, path)
uv run python scripts/run_evals.py --verbose

# Single category
uv run python scripts/run_evals.py --category search --verbose
uv run python scripts/run_evals.py --category skill_gap
uv run python scripts/run_evals.py --category path
```

### Prerequisites

- `.env.local` with `OPENAI_API_KEY`
- `uv sync --dev` (installs DeepEval)

### How It Works

1. Loads Golden Dataset (`evals/datasets/{category}_golden.json`)
2. Builds prompt from `app/prompts/{category}.md` + pre-defined `retrieval_context`
3. Calls GPT-4o-mini to generate response
4. DeepEval measures Faithfulness and Hallucination against retrieval context
5. Exit code 0 if all thresholds pass, 1 if any fail

---

## RAG Eval — Retrieval Quality

Evaluates the full search pipeline: Embed -> Qdrant Hybrid Search -> Rerank -> Results.
Measures retrieval quality against Golden Datasets. **Not run in CI** (requires Qdrant).

### Metrics

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Hit Rate@10 | >= 0.60 | At least one expected course in top-10 results |
| MRR | >= 0.40 | Mean Reciprocal Rank of first relevant result |
| NDCG@10 | (info only) | Normalized Discounted Cumulative Gain |

### Run Locally

```bash
cd ai

# All categories (default: reranker=none, formatter=json)
uv run python scripts/run_rag_evals.py --verbose

# Single category
uv run python scripts/run_rag_evals.py --category search --verbose

# Strategy comparison (ADR-012-5: Reranker)
uv run python scripts/run_rag_evals.py --reranker none -v
uv run python scripts/run_rag_evals.py --reranker heuristic -v
uv run python scripts/run_rag_evals.py --reranker cross-encoder -v

# Strategy comparison (ADR-012-6: Formatter)
uv run python scripts/run_rag_evals.py --formatter json -v
uv run python scripts/run_rag_evals.py --formatter toon -v
```

### Prerequisites

- Qdrant running locally (`docker compose up -d`)
- Data seeded (`uv run python scripts/seed_data.py`)
- `.env.local` with `OPENAI_API_KEY` and `QDRANT_URL`

### How It Works

1. Loads Golden Dataset with `expected_courses` (actual Qdrant course titles)
2. Runs `SearchCoursesUseCase` with the specified reranker/formatter strategy
3. Compares retrieved course titles against expected courses
4. Computes Hit Rate@10, MRR, NDCG@10
5. Exit code 0 if all thresholds pass, 1 if any fail

---

## Golden Datasets

Location: `evals/datasets/`

| File | Category | Test Cases | Has `expected_courses` | Has `retrieval_context` |
|------|----------|------------|------------------------|------------------------|
| `search_golden.json` | Search Agent | 20 | Yes (for RAG eval) | Yes (for CI eval) |
| `skill_gap_golden.json` | Skill Gap Agent | 5 | No | Yes (for CI eval) |
| `path_golden.json` | Path Agent | 5 | No | Yes (for CI eval) |

### Dataset Structure

```json
{
  "test_id": "search_001",
  "query": "I want to learn Python as a beginner",
  "expected_agent": "Search Agent",
  "expected_courses": ["Python for the Absolute Beginner"],
  "retrieval_context": [
    "{\"title\": \"Python for Everybody Specialization\", ...}"
  ]
}
```

- `retrieval_context`: Pre-defined context for CI eval (no Qdrant needed)
- `expected_courses`: Expected course titles from Qdrant for RAG eval

### Updating Golden Datasets

When updating `expected_courses`, ensure titles match **actual Qdrant data**:

```bash
# Verify what Qdrant actually returns for a query
cd ai
uv run python -c "
import asyncio
from app.config.container import build_container
from app.config.settings import get_settings
from app.domain.usecases.search_courses import SearchCoursesUseCase, SearchQuery
from app.infrastructure.reranking import create_reranker
from app.infrastructure.formatters import create_formatter

async def check(query: str):
    container = build_container()
    settings = get_settings()
    usecase = SearchCoursesUseCase(
        vector_store=container.vector_store,
        embedding=container.embedding,
        reranker=create_reranker('none'),
        formatter=create_formatter('json'),
    )
    result = await usecase.execute(SearchQuery(query=query, limit=10, threshold=settings.SIMILARITY_THRESHOLD))
    for c in result.courses:
        print(f'  - {c.title}')

asyncio.run(check('YOUR QUERY HERE'))
"
```

---

## pytest Benchmarks

DeepEval benchmarks can also be run via pytest:

```bash
cd ai

# All benchmarks
uv run pytest evals/benchmarks/ -v

# Single category
uv run pytest evals/benchmarks/test_search_eval.py -v
```

---

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/llm-eval.yml`) runs CI Eval on PRs:

- **Trigger**: PR to `develop` or `main` modifying `ai/app/**` or `ai/evals/**`
- **Action**: Runs `uv run python scripts/run_evals.py --verbose`
- **Gate**: Tier 1 thresholds must pass for merge
- **PR Comment**: Posts eval summary with pass/fail status
