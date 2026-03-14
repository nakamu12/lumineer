# Lumineer

Coursera コースデータ (6,645件) を活用し、AI エージェントによるコース検索・スキル分析・学習パス生成を提供する Web アプリケーション。学びの道を照らす Intelligent Course Discovery System。

## Architecture (3-Layer)

| Layer | Tech | Pattern |
|-------|------|---------|
| Frontend | Bun + React (Vite) + Shadcn UI + Tailwind | Feature-based |
| API Layer | Bun + Hono (TypeScript) | Clean Architecture |
| AI Processing | Python + Litestar/FastAPI | OpenAI Best Practices |

依存方向: Frontend → API Layer → AI Processing → Qdrant / OpenAI

## Key Commands

```bash
# Frontend
cd frontend && bun install && bun dev

# API Layer
cd backend && bun install && bun dev

# AI Processing
cd ai && uv sync && uv run python main.py

# Lint & Type Check
cd frontend && bun run lint && bun run typecheck
cd ai && ruff check . && ruff format . && mypy .

# Test
cd ai && pytest
cd frontend && bun test

# Docker (全サービス起動)
docker compose up
```

## Git Workflow

- **Branch naming**: `LM{IssueID}-{type}/{scope}-{detail}`
  - type: feature / fix / hotfix / refactor / docs / test / chore
  - scope: frontend / backend / rag / agents / data / infra / mcp
  - 例: `LM0001-feature/rag-hybrid_search`
- **Flow**: develop → feature branch → PR → CI → develop → main
- **PR**: `Closes #{IssueID}` で Issue 自動クローズ
- **Commit**: 日本語 OK、簡潔に

## Project Structure

```text
capstone/
├── frontend/          # React + Shadcn UI (Feature-based)
├── backend/           # Hono + TypeScript (Clean Architecture)
├── ai/                # Python (OpenAI Best Practices)
│   ├── app/
│   │   ├── agents/    # エージェント定義
│   │   ├── tools/     # Tool functions
│   │   ├── prompts/   # プロンプトテンプレート (.md)
│   │   ├── guardrails/# 5層防衛
│   │   ├── domain/    # entities, ports, usecases
│   │   ├── infrastructure/ # adapters
│   │   └── interfaces/# API routes
│   ├── data/          # raw, processed, embeddings
│   ├── evals/         # Golden Dataset, benchmarks
│   └── scripts/       # seed, eval, export
├── docs/              # 要件定義、ADR
├── infra/             # Terraform IaC
└── rules/             # デザインシステム等リファレンス
```

## Language Policy

- **All code in English**: variable names, function names, class names, comments, docstrings, error messages
- **All UI text in English**: labels, buttons, placeholders, toasts, error messages shown to users
- **Commit messages**: English or Japanese (both OK)
- **Internal docs** (requirements.md, ADR etc.): Japanese OK (developer reference)

## Core Rules

- Factory パターンでエンティティ生成（`new Entity()` 禁止）
- Port/Adapter で外部依存を抽象化（LLM, VectorDB, Embedding）
- Strategy パターンで Reranker / Formatter を切替可能に
- プロンプトは `prompts/*.md` に外部化（コード内にハードコード禁止）
- ガードレールは `@input_guardrail` / `@output_guardrail` デコレータで並列実行
- 環境変数は Pydantic Settings で管理（`.env` ファイルは Dev のみ）
- Public リポジトリ: API Key は GitHub Secrets、コードに含めない

## References

- 要件定義: @docs/requirements.md
- ADR: @docs/adr.md
- デザインシステム: @rules/15-styleguide.md
