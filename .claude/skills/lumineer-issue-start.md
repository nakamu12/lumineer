---
name: lumineer-issue-start
description: >
  Lumineer プロジェクトで新しい Issue の作業を開始するワークフローを自動化するスキル。
  Issue 確認・ブランチ作成・git worktree セットアップ・GitHub Project への登録・
  ステータスを "In Progress" に設定するまでの一連の手順を一括で行う。
  ユーザーが「ブランチを切る」「Issue を始める」「作業開始」「/lumineer-issue-start」
  と言った場合や、新しい機能・修正・チョアの実装に着手しようとしている場面で必ず使用すること。
---

# Lumineer Issue Start ワークフロー

## 概要

以下の手順を順番に実行して、新しい Issue の作業環境を整える。

1. 必要な情報を収集する
2. GitHub Issue を確認（または新規作成）する
3. ブランチ名を構築する
4. git worktree を作成して開発環境を準備する
5. GitHub Project にカンバン登録し "In Progress" にする

---

## Step 1: 情報を収集する

以下の情報が引数で与えられていない場合はユーザーに確認する。
全て揃っていればそのまま進む。

| 項目 | 説明 | 例 |
|------|------|-----|
| `issue_number` | 既存 Issue 番号（新規の場合は「new」） | `5`, `42`, `new` |
| `type` | ブランチ種別 | `feature` / `fix` / `hotfix` / `refactor` / `docs` / `test` / `chore` |
| `scope` | 対象領域 | `frontend` / `backend` / `rag` / `agents` / `data` / `infra` / `mcp` |
| `detail` | 内容の要約（snake_case） | `hybrid_search`, `settings_page` |

複数 scope にまたがる場合は `+` で連結: `frontend+backend`

---

## Step 2: Issue の確認または新規作成

### 既存 Issue の場合
```bash
gh issue view {issue_number}
```
Issue のタイトルと状態を確認する。

### 新規 Issue の場合
ユーザーに Issue タイトルと本文（概要・作業内容）を確認してから作成する:
```bash
gh issue create --title "{title}" --body "{body}"
```
作成後、発行された Issue 番号を `issue_number` として使用する。

---

## Step 3: ブランチ名とワークツリーパスの構築

### ブランチ名
```
LM{NNNN}-{type}/{scope}-{detail}
```
- `NNNN` は Issue 番号を 4 桁ゼロ埋め（例: 5 → `0005`）
- `detail` は snake_case

**例:**
- Issue #5, chore, infra, docker_compose → `LM0005-chore/infra-docker_compose`
- Issue #8, feature, rag, hybrid_search → `LM0008-feature/rag-hybrid_search`

### ワークツリーディレクトリ名
ブランチ名の `/` を `-` に変換した名前を使用する:
```
LM{NNNN}-{type}-{scope}-{detail}
```

**例:** `LM0005-chore-infra-docker_compose`

### ワークツリーパス
プロジェクトルートの **1 つ上の階層** に `worktree/` ディレクトリを作成する:
```
{project_root}/../worktree/{worktree_dir_name}
```

プロジェクトルートを確認:
```bash
git rev-parse --show-toplevel
```

---

## Step 4: ワークツリー作成と開発環境セットアップ

### 4-1. develop を最新化してワークツリーを作成
```bash
# develop を最新化
git fetch origin develop
git checkout develop
git pull origin develop

# worktree ディレクトリを確保（初回のみ）
mkdir -p {project_root}/../worktree

# worktree を作成（develop から新しいブランチを分岐）
git worktree add {worktree_path} -b {branch_name} origin/develop
```

### 4-2. リモートへ push
```bash
cd {worktree_path}
git push -u origin {branch_name}
```

### 4-3. scope に応じた依存関係インストール

scope に応じて以下のコマンドを実行する（不要な scope はスキップ）:

| scope | コマンド | 対象ディレクトリ |
|-------|---------|----------------|
| `frontend` | `bun install` | `{worktree_path}/frontend/` |
| `backend` | `bun install` | `{worktree_path}/backend/` |
| `rag` / `agents` / `data` | `uv sync` | `{worktree_path}/ai/` |
| `infra` | なし | — |
| `mcp` | `uv sync` | `{worktree_path}/ai/` |

対象ディレクトリが存在する場合のみ実行する。

---

## Step 5: GitHub Project にカンバン登録

### 5-1. Issue の node_id を取得
```bash
gh api repos/nakamu12/lumineer/issues/{issue_number} --jq '.node_id'
```

### 5-2. プロジェクトに Issue を追加
```bash
gh api graphql -f query='
mutation {
  addProjectV2ItemById(input: {
    projectId: "PVT_kwHOArXseM4BRwSj"
    contentId: "{ISSUE_NODE_ID}"
  }) {
    item { id }
  }
}'
```
レスポンスから `item.id`（`PVTI_...`）を取得する。

### 5-3. ステータスを "In Progress" に設定
```bash
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwHOArXseM4BRwSj"
    itemId: "{ITEM_ID}"
    fieldId: "PVTSSF_lAHOArXseM4BRwSjzg_fT98"
    value: { singleSelectOptionId: "04d254ff" }
  }) {
    projectV2Item { id }
  }
}'
```

---

## 完了メッセージ

全ステップが成功したら以下の情報をまとめて報告する:

```
✅ 作業準備完了

Issue      : #{issue_number} {issue_title}
Branch     : {branch_name}
Worktree   : {worktree_path}
Project    : In Progress に設定済み

作業ディレクトリ: cd {worktree_path}
完了後は PR を作成し、本文に `Closes #{issue_number}` を記載してください。
```

---

## ワークツリーのクリーンアップ（PR マージ後）

PR マージ後に不要になったワークツリーを削除する:

```bash
# プロジェクトルートに戻る
cd {project_root}

# ワークツリーを削除
git worktree remove {worktree_path}

# ローカルブランチを削除
git branch -d {branch_name}
```

---

## プロジェクト固定値（参照用）

| 項目 | 値 |
|------|-----|
| GitHub owner | `nakamu12` |
| GitHub repo | `lumineer` |
| Project ID | `PVT_kwHOArXseM4BRwSj` |
| Status field ID | `PVTSSF_lAHOArXseM4BRwSjzg_fT98` |
| Backlog | `afba2708` |
| To Do | `04a82eb6` |
| **In Progress** | **`04d254ff`** |
| Review | `69a7603d` |
| Done | `448bcca5` |
