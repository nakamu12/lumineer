---
description: Git ワークフローとタスク管理ルール
---

# Workflow Rules

## ブランチ命名

```
LM{IssueID}-{type}/{scope}-{detail}
```

- **prefix**: `LM`（Lumineer）
- **IssueID**: 4桁 Issue 番号（例: `0001`）
- **type**: feature / fix / hotfix / refactor / docs / test / chore
- **scope**: frontend / backend / rag / agents / data / infra / mcp
- **detail**: snake_case

例: `LM0001-feature/rag-hybrid_search`, `LM0010-feature/frontend+backend-search_results`

## ブランチフロー

```
通常:   develop → feature branch → PR → CI → develop → main
hotfix: main → hotfix branch → PR → main + develop マージ
```

- main への直接 push 禁止
- feature branch は develop から分岐

## PR 規約

- タイトル: 簡潔に（70文字以内）
- 本文に `Closes #{IssueID}` を含めて Issue 自動クローズ
- CI (lint + test) が通るまでマージしない

## コミット

- 日本語 OK
- 1コミット = 1つの論理的変更
- API Key やシークレットを含むコミットは禁止

## タスク管理

- 全タスクは GitHub Issues で採番
- GitHub Projects カンバン: Backlog → To Do → In Progress → Review → Done
- PR マージで Issue 自動クローズ + カンバン自動移動
