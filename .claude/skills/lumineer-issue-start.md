---
name: lumineer-issue-start
description: >
  Lumineer プロジェクトで新しい Issue の作業を開始するワークフローを自動化するスキル。
  ブランチ作成・リモート push・GitHub Project へのカンバン登録・ステータスを "In Progress"
  に設定するまでの一連の手順を一括で行う。
  ユーザーが「ブランチを切る」「Issue を始める」「作業開始」「/lumineer-issue-start」
  と言った場合や、新しい機能・修正・チョアの実装に着手しようとしている場面で使用すること。
---

# Lumineer Issue Start ワークフロー

## 概要

以下の手順を順番に実行して、新しい Issue の作業環境を整える。

1. 必要な情報を収集する
2. GitHub Issue を確認（または新規作成）する
3. ブランチを作成して push する
4. GitHub Project にカンバン登録し "In Progress" にする

---

## Step 1: 情報を収集する

以下の情報が引数で与えられていない場合はユーザーに確認する。
全て揃っていればそのまま進む。

| 項目 | 説明 | 例 |
|------|------|-----|
| `issue_number` | 既存 Issue 番号（新規の場合は「new」） | `1`, `42`, `new` |
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

## Step 3: ブランチ名の構築

以下の形式でブランチ名を組み立てる:

```
LM{NNNN}-{type}/{scope}-{detail}
```

- `NNNN` は Issue 番号を4桁ゼロ埋め（例: 1 → `0001`, 42 → `0042`）
- `detail` は snake_case

**例:**
- Issue #1, feature, infra, terraform_gcp_setup → `LM0001-feature/infra-terraform_gcp_setup`
- Issue #10, fix, agents, triage_routing → `LM0010-fix/agents-triage_routing`
- Issue #3, feature, frontend+backend, search_results → `LM0003-feature/frontend+backend-search_results`

---

## Step 4: ブランチ作成と push

`develop` ブランチから分岐させる:

```bash
git checkout develop
git pull origin develop
git checkout -b {branch_name}
git push -u origin {branch_name}
```

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

Issue   : #{issue_number} {issue_title}
Branch  : {branch_name}
Project : In Progress に設定済み

次のステップ: 実装を開始してください。
完了後は PR を作成し、本文に `Closes #{issue_number}` を記載してください。
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
