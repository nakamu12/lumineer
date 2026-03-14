---
description: RAG パイプラインと Strategy パターンのルール
globs: ai/app/infrastructure/**
---

# RAG Pipeline Rules

## 検索フロー

```
Query → メタデータフィルタ → Hybrid Search (Dense + Sparse)
  → RRF スコア統合 → Reranking (Strategy) → Result Selection
  → Context Assembly (Formatter) → Agent に返却
```

## Hybrid Search

- **Dense**: text-embedding-3-large（3072次元）による意味検索
- **Sparse**: Qdrant Sparse Vector（BM25 相当）によるキーワードマッチ
- **スコア統合**: RRF (Reciprocal Rank Fusion)。Qdrant ネイティブ対応

## Reranker（Strategy パターン）

```python
# ✅ BaseReranker を継承し、Strategy で切替
class BaseReranker:
    def rerank(self, query: str, results: list[dict], top_k: int) -> list[dict]:
        raise NotImplementedError

class NoReranker(BaseReranker): ...        # パススルー
class HeuristicReranker(BaseReranker): ... # α×relevance + β×rating + γ×enrolled
class CrossEncoderReranker(BaseReranker): ... # Neural Re-ranking
```

- 切替: 環境変数 `RERANKER_STRATEGY` or UI 設定画面
- 新しい Strategy 追加時は `BaseReranker` を継承するだけ

## Formatter（Strategy パターン）

- **JSON**: LLM 理解度が確実。トークン消費が多い
- **TOON**: トークン約 50% 削減。同じ予算でより多くの結果を含められる
- 切替: 環境変数 `CONTEXT_FORMAT` or UI 設定画面

## Result Selection

- Top-k: リランキング後の上位 k 件（デフォルト k=10）
- Threshold: 類似度スコアが閾値未満の結果を除外
- 件数不足時: Corrective RAG（クエリ再構成 → 再検索）

## Ingestion（初回のみ）

```
CSV → LLM前処理 (GPT-4o-mini) → Embedding → Qdrant
```

- 前処理: Skills 補完 + Description 正規化
- コレクション: 単一コレクション + メタデータフィルタ
- `scripts/seed_data.py` で実行

## 禁止事項

- ハードコードされたフィルタ条件（メタデータフィルタは動的に構築）
- Qdrant クライアントを `infrastructure/` 以外から直接呼び出す
- Embedding モデルの直接呼び出し（Port 経由で抽象化）
