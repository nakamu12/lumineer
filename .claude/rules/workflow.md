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
- **develop への直接コミット禁止**: 全ての変更は feature branch → PR 経由でマージする
- feature branch は develop から分岐

## PR 規約

- タイトル: 簡潔に（70文字以内）
- 本文に `Closes #{IssueID}` を含めて Issue 自動クローズ
- CI (lint + test) が通るまでマージしない

## コミット

- 日本語 OK
- 1コミット = 1つの論理的変更
- API Key やシークレットを含むコミットは禁止

## 鉄則: Issue 先行 + worktree 必須

1. **Issue 先行**: ブランチ作成前に必ず GitHub Issue を立て、その Issue 番号をブランチ名に使用する。無関係なタスクに既存 Issue の番号を流用しない
2. **メインリポジトリは常に develop**: メインリポジトリで `git checkout` して他ブランチに切り替えない。feature 作業は必ず `git worktree` で行う
3. **develop への直接コミット禁止**: どんな小さな変更でも feature branch → PR 経由

## git worktree（必須）

全ての feature 作業は `git worktree` を使用する。

### worktree の格納場所

```
{project_root}/../worktree/{worktree_dir}/
```

例: プロジェクトが `capstone/lumineer/` の場合 → `capstone/worktree/LM0005-chore-infra-docker_compose/`

### ディレクトリ名の規則

ブランチ名の `/` を `-` に置換する:
- ブランチ: `LM0005-chore/infra-docker_compose`
- ディレクトリ: `LM0005-chore-infra-docker_compose`

### 作業開始（/lumineer-issue-start スキルで自動化）

```bash
git worktree add ../worktree/LM{NNNN}-{type}-{scope}-{detail} \
  -b LM{NNNN}-{type}/{scope}-{detail} origin/develop
cd ../worktree/LM{NNNN}-{type}-{scope}-{detail}
git push -u origin LM{NNNN}-{type}/{scope}-{detail}
```

### 作業終了（PR マージ後）

```bash
git worktree remove ../worktree/{worktree_dir}
git branch -d LM{NNNN}-{type}/{scope}-{detail}
```

## タスク管理

- 全タスクは GitHub Issues で採番
- GitHub Projects カンバン: Backlog → To Do → In Progress → Review → Done
- PR マージで Issue 自動クローズ + カンバン自動移動
- 作業開始時は `/lumineer-issue-start` スキルで一括セットアップ
