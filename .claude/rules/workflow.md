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

## 検証方法: インフラとアプリを分離

worktree で `docker compose up` するとプロジェクト名が変わり、ポート競合・コンテナ重複が発生する。
`docker-compose.yml` に `name: lumineer` を設定し、アプリサービスを `profiles: [app]` で分離することで解決する。

### Docker Compose コマンド早見表

```bash
# インフラのみ起動（worktree 作業中は常にこれ）
docker compose up -d                       # postgres + qdrant のみ起動

# フルスタック起動（develop でのフル統合テスト時）
docker compose --profile app up -d         # 全サービス起動

# Observability も含めて起動
docker compose --profile app --profile observability up -d
```

### 原則

| 層 | どこで動かすか | 方法 |
|---|---|---|
| **インフラ** (PostgreSQL, Qdrant) | メインリポジトリ (lumineer/) | `docker compose up -d` |
| **アプリ** (backend, frontend, ai) | worktree | `bun dev` / `uv run python main.py` で直接起動 |

### 検証レベル

| レベル | タイミング | 方法 | Docker 必要 |
|---|---|---|---|
| lint + typecheck + unit test | 毎回（PR 前に必須） | worktree 内で実行 | 不要 |
| 手動 API テスト | 必要な時だけ | worktree から `bun dev` + curl | インフラのみ |
| フル統合テスト | develop マージ後 | develop で `docker compose --profile app up -d` | 全コンテナ |

### 手動検証の手順

```bash
# 1. メインリポジトリでインフラだけ起動（常時維持）
cd lumineer
docker compose up -d   # postgres + qdrant のみ。名前が lumineer-* に固定される

# 2. worktree で静的検証（Docker 不要）
cd ../worktree/LM{NNNN}-{type}-{scope}-{detail}
cd backend && bun run lint && bun run typecheck && bun test

# 3. 手動検証が必要な場合、worktree からアプリを直接起動
#    Gateway → Backend → AI の順に起動（Frontend は Vite proxy で Gateway 経由）
cd gateway && BACKEND_URL=http://localhost:3001 bun dev  # localhost:3000
cd backend && bun dev             # localhost:3001
cd frontend && bun dev            # localhost:5173 (Vite proxy → :3000)
cd ai && uv run python main.py    # localhost:8001
# → ブラウザで localhost:5173 を開いて動作確認、終わったら Ctrl+C
```

### ローカル起動用 .env.local の設定

`.env.local` はルートに 1 つだけ置く（サービスごとに作らない）。

- `backend/bun dev` は `--env-file=../.env.local` でルートの `.env.local` を読む
- `ai/uv run python main.py` は Pydantic Settings がルートの `.env.local` を絶対パスで読む

```bash
# ルートの .env.local に QDRANT_URL / DATABASE_URL を追記するだけ
# （ポートを変更した場合はここで調整）
QDRANT_URL=http://localhost:6333
DATABASE_URL=postgres://lumineer:lumineer@localhost:5432/lumineer
```

## 開発フロー（実装時の必須手順）

コード実装タスクでは以下の順序を必ず守る:

```
1. TDD: RED → GREEN → REFACTOR（テストファースト）
   - /tdd スキルで開始
   - 先にテストを書いて失敗を確認（RED）
   - 最小限の実装でテストを通す（GREEN）
   - リファクタリング（REFACTOR）

2. 実装完了後: テスト実行
   - bun test / pytest で全テスト通過を確認

3. 実装完了後: Code Review + Security Review（並列サブエージェント）
   - code-reviewer サブエージェントで品質・アーキテクチャ準拠を確認
   - security-reviewer サブエージェントで OWASP Top 10・秘密漏洩・PII を確認
   - 2つは独立なので必ず並列実行する
   - 指摘があれば修正してから PR を作成
```

**省略禁止**: テストだけ通して Review を飛ばさない。Review で指摘がなくても毎回実行する。

## タスク管理

- 全タスクは GitHub Issues で採番
- GitHub Projects カンバン: Backlog → To Do → In Progress → Review → Done
- PR マージで Issue 自動クローズ + カンバン自動移動
- 作業開始時は `/lumineer-issue-start` スキルで一括セットアップ
