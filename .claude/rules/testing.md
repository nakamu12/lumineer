---
description: テスト戦略と評価パイプラインのルール
globs:
  - ai/tests/**
  - ai/evals/**
  - frontend/**/*.test.*
  - backend/**/*.test.*
---

# Testing Rules

## 3 層テスト構成

```
Layer 1: Unit Tests (Vitest / pytest) — 毎コミット
Layer 2: RAG Evaluation (DeepEval + Golden Dataset) — LLM 関連変更時
Layer 3: E2E Agent Tests (LLM-as-Judge) — リリース前
```

## Layer 1: Unit Tests

```bash
# Python (AI Processing)
cd ai && pytest

# Frontend & Backend (TypeScript)
cd frontend && bun test
cd backend && bun test
```

### フレームワーク選定

| レイヤー | フレームワーク | 理由 |
|---------|--------------|------|
| Frontend | **Vitest** | Vite プロジェクトとネイティブ統合。`vite.config.ts` に設定統合可能。TypeScript をそのまま実行 |
| Backend | **Vitest** | 同上。Jest 互換 API で移行コスト低 |
| AI Processing | **pytest** | Python エコシステム標準 |

### Vitest の基本

```typescript
// ✅ Vitest のインポート（Jest API 互換）
import { describe, it, expect, vi } from "vitest"

// モック（vi.fn() を使用。jest.fn() ではない）
const mockFn = vi.fn()
vi.mock("@/lib/hooks/useApi")
```

- Formatter, Reranker, メタデータフィルタ等は必ず Unit Test を書く
- 外部依存（Qdrant, OpenAI）はモック化（`vi.mock()`）
- Port/Adapter パターンにより、Port をモックするだけでテスト可能

## Layer 2: RAG Evaluation

- **Golden Dataset**: 80-100 件（手動 25 件 + LLM 逆生成 50-70 件）
- **配置**: `evals/datasets/` (JSON)
- **実行**: `scripts/run_evals.py`

### 必須メトリクス（CI/CD ゲート）

| メトリクス | 説明 |
|-----------|------|
| Hit Rate@10 | 正解コースが top-10 に含まれるか |
| Hallucination | 存在しないコースの創作を検知 |
| Faithfulness | コンテキスト情報のみの正確な引用 |

### Strategy 比較用メトリクス

- MRR, NDCG@10: ランキング品質
- Precision@10, Answer Relevancy: 改善指針

## CI/CD 統合

```yaml
# Stage 1: 全 Push で実行
Frontend: prettier --check → eslint → tsc --noEmit → vitest
Backend:  prettier --check → eslint → tsc --noEmit → vitest
AI:       ruff format --check → ruff check → mypy → pytest

# Stage 2: LLM 関連変更時のみ実行
paths:
  - 'ai/app/agents/**'
  - 'ai/app/tools/**'
  - 'ai/app/prompts/**'
  - 'ai/app/infrastructure/**'
```

- Tier 1 閾値未満 → マージブロック
- フロントエンド・ドキュメント変更では LLM Eval は走らない
