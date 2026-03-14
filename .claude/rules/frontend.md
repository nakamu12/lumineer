---
description: Frontend (React + Shadcn UI + Tailwind) のルール
globs: frontend/**
---

# Frontend Rules

## Feature-based 構成

```
frontend/src/
├── lib/              # 共通パーツ
│   ├── ui/           # Shadcn UI コンポーネント（自動生成）
│   ├── layout/       # Header, PageLayout
│   ├── hooks/        # useApi, useDebounce
│   └── types/        # 共通型定義
├── features/         # ドメイン別機能
│   ├── search/       # コース検索
│   ├── recommend/    # 推薦・学習パス
│   └── chat/         # チャット UI
└── app/              # エントリポイント・ルーティング
```

## 配置ルール

- 特定 feature でしか使わないコンポーネント → `features/{name}/components/`
- 2つ以上の feature で共有 → `lib/ui/` or `lib/layout/`
- API 呼び出しフック → `features/{name}/hooks/` or `lib/hooks/`
- 型定義が feature 固有 → `features/{name}/types.ts`

## Shadcn UI + Tailwind

- UI プリミティブは Shadcn UI を使う（独自 UI コンポーネントを再発明しない）
- スタイリングは Tailwind CSS のユーティリティクラスのみ。CSS ファイル追加禁止
- デザインシステムの色・間隔は `tailwind.config` のテーマを参照
- 詳細は @rules/15-styleguide.md

## デザイン原則

- **ミニマル**: 余白を活かし、情報密度を抑える
- **段階的開示**: 最初は最低限、展開で詳細
- **レスポンシブ**: Tailwind CSS breakpoints (sm / md / lg)

## ランタイム

- **Bun** でインストール・ビルド・テスト（npm / yarn 禁止）
- `bun install`, `bun dev`, `bun test`, `bun run build`

## API Layer との通信

- REST + SSE（Server-Sent Events でストリーミング応答）
- AI Processing Layer を直接呼ばない。必ず API Layer 経由
