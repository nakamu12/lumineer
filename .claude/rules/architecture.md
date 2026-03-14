---
description: 3層アーキテクチャと依存方向の基本ルール
---

# Architecture Rules

## 3-Layer 分離

```
Frontend (React) → API Layer (Hono/TS) → AI Processing (Python) → Qdrant / OpenAI
```

- レイヤー間通信は HTTP (REST + SSE) のみ。直接 import 禁止
- Frontend は AI Processing を直接呼ばない。必ず API Layer を経由する
- AI Processing は Frontend の存在を知らない

## 依存方向（各レイヤー内部）

```
interfaces/ → usecases/ → ports/ ← infrastructure/
```

- `domain/` は外部ライブラリに依存しない（Pure TypeScript / Pure Python）
- `infrastructure/` は `domain/ports/` のインターフェースを実装する
- `interfaces/` はフレームワーク固有コード（Hono Router, Litestar Route）を含む

## 必須パターン

- **Factory パターン**: エンティティ生成は Factory 経由。`new Entity()` 直接呼び出し禁止
- **Port/Adapter**: LLM, VectorDB, Embedding は Port で抽象化。実装は `infrastructure/` に配置
- **Strategy パターン**: Reranker, Formatter は Strategy で切替可能に設計
- **DI (Dependency Injection)**: `config/container.py` or `config/di.ts` で注入

## ファイル配置の原則

- ビジネスロジック → `domain/usecases/`
- 外部 API 呼び出し → `infrastructure/`
- HTTP ルーティング → `interfaces/api/`
- 設定・環境変数 → `config/`
- プロンプト → `prompts/*.md`（コード内ハードコード禁止）
