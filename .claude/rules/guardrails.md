---
description: 5層防衛ガードレールの実装ルール
globs: ai/app/guardrails/**
---

# Guardrail Rules

## 5層防衛アーキテクチャ

| 層 | 名前 | 主な責務 |
|----|------|---------|
| L1 | Input Guards | インジェクション検出, Toxicity, Off-topic, PII マスキング |
| L2 | Data Guards | Context Window 保護, RAG データ検証 |
| L3 | Agent Guards | Tool Permission, Persona Lock, ループ検出 |
| L4 | Output Guards | ハルシネーション検出, プライバシー保護, PII 復元 |
| L5 | Economic Guards | トークン制限, レート制限, コスト追跡 |

## デコレータによる並列実行

```python
# ✅ @input_guardrail / @output_guardrail で宣言的に適用
@input_guardrail
async def injection_detector(ctx, agent, input):
    # LLM 判定でインジェクション検出
    ...

@output_guardrail
async def hallucination_checker(ctx, agent, output):
    # DB 照合 + LLM Verifier の 2 段構成
    ...
```

- ガードレールは Agent 定義時に `input_guardrails=[]`, `output_guardrails=[]` で付与
- 複数ガードレールは並列実行（レイテンシ最小化）

## ディレクトリ構成

```
guardrails/
├── input/
│   ├── injection_detector.py
│   ├── toxicity_filter.py
│   ├── offtopic_detector.py
│   └── pii_sanitizer.py     # Presidio
├── output/
│   ├── hallucination_checker.py  # DB照合 + LLM Verifier
│   ├── privacy_filter.py
│   └── pii_restorer.py
└── system/
    ├── rate_limiter.py
    └── cost_tracker.py
```

## 設計原則

- **フェイルセーフ**: 判定が曖昧な場合は拒否（安全側に倒す）
- **観測可能**: 全トリガーを Langfuse にログ
- **テスト可能**: Red Team テストケースを Golden Dataset に含む
- 各ガードレールは独立してテスト可能な単一関数

## ハルシネーション検出の 2 段構成

```
LLM 出力 → Stage 1: DB 照合（コスト 0）→ Stage 2: LLM Verifier（並列）
```

- Stage 1: 出力に含まれるコース名を `retrieved_courses` と照合
- Stage 2: 「この回答はコンテキストに基づいているか」を別 LLM で検証
