---
description: API Layer (Hono/TypeScript) のクリーンアーキテクチャルール
globs: backend/**
---

# API Layer Rules

## Clean Architecture 構成

```
backend/src/
├── domain/          # 核心（外部依存なし）
│   ├── entities/    # Course, LearningPath, SkillGap
│   ├── ports/       # LLMPort, VectorStorePort, EmbeddingPort
│   └── usecases/    # search_courses, analyze_skill_gap
├── infrastructure/  # 外部接続の具体実装
│   ├── llm/         # AI Processing Layer への HTTP クライアント
│   ├── vectordb/    # Qdrant アダプタ
│   ├── embeddings/  # text-embedding-3-large アダプタ
│   ├── reranking/   # Strategy: None / Heuristic / CrossEncoder
│   └── formatters/  # Strategy: JSON / TOON
├── interfaces/      # 入力アダプタ
│   ├── api/         # Hono REST API Router
│   └── mcp/         # MCP Server（予定）
└── config/          # 設定・DI
```

## 依存方向

```
interfaces/ → usecases/ → ports/ ← infrastructure/
```

- `domain/` は Hono, qdrant-js 等のライブラリに依存しない
- `infrastructure/` は `domain/ports/` の型を実装する
- `interfaces/api/` のみが Hono の `Context`, `Hono` をインポートする

## Hono パターン

```typescript
// ✅ Router は interfaces/api/ に配置
// ✅ ビジネスロジックは usecase を呼ぶだけ
app.get('/courses/:id', async (c) => {
  const result = await getCourseUseCase.execute(c.req.param('id'));
  return c.json(result);
});

// ❌ Router 内にビジネスロジックを書かない
app.get('/courses/:id', async (c) => {
  const data = await qdrant.search(...); // infrastructure 直接呼び出し
  const filtered = data.filter(...);     // ロジック直書き
  return c.json(filtered);
});
```

## API Layer の役割

- リクエスト検証・レスポンス整形
- AI Processing Layer への HTTP プロキシ
- 設定管理（リランカー切替、検索パラメータ等）
- **AI Processing を直接呼ぶのは API Layer のみ**
