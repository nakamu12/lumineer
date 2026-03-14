#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# gh-task.sh — GitHub Issue 作成 + ブランチ作成
#
# 使い方: gh-task.sh "<type>" "<scope>" "<説明文>" ["<ブランチ名>"]
# 例:     gh-task.sh "feature" "rag" "Hybrid Search 実装" "hybrid-search"
#
# VS Code tasks.json から呼ばれることを想定。
# omnicore-app の notion-task.sh に相当する GitHub 版。
# =============================================================================

TASK_TYPE="${1:?type を指定してください（feature/fix/hotfix/refactor/docs/test/chore）}"
TASK_SCOPE="${2:?scope を指定してください（frontend/backend/rag/agents/data/infra/mcp）}"
TASK_DESC="${3:?説明文を指定してください}"
BRANCH_SUFFIX="${4:-}"

GIT_BASE_BRANCH="${GIT_BASE_BRANCH:-develop}"

# --- バリデーション ---

VALID_TYPES="feature fix hotfix refactor docs test chore"
VALID_SCOPES="frontend backend rag agents data infra mcp"

validate() {
  local value="$1" valid="$2" label="$3"
  if ! echo "$valid" | grep -qw "$value"; then
    echo "エラー: 不正な ${label}: ${value}" >&2
    echo "  許可: ${valid}" >&2
    exit 2
  fi
}

validate "$TASK_TYPE" "$VALID_TYPES" "type"
validate "$TASK_SCOPE" "$VALID_SCOPES" "scope"

# --- gh CLI チェック ---

if ! command -v gh &>/dev/null; then
  echo "エラー: gh CLI がインストールされていません" >&2
  echo "  brew install gh && gh auth login" >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "エラー: gh にログインしていません。gh auth login を実行してください" >&2
  exit 1
fi

# --- Git 状態チェック ---

echo "Git 状態をチェック中..." >&2

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "エラー: Git リポジトリ内で実行してください" >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "エラー: 未コミットの変更があります。先にコミットしてから実行してください。" >&2
  echo "" >&2
  echo "未コミットのファイル:" >&2
  git status --porcelain >&2
  exit 1
fi

echo "Git 状態 OK" >&2

# --- ブランチ名サフィックス生成 ---

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[[:space:]]+/-/g' \
    | sed -E 's/[^a-z0-9_-]+//g' \
    | sed -E 's/^-+//; s/-+$//' \
    | cut -c1-48
}

if [[ -n "$BRANCH_SUFFIX" ]]; then
  BR_DETAIL="$(slugify "$BRANCH_SUFFIX")"
else
  BR_DETAIL="$(slugify "$TASK_DESC")"
fi
[[ -z "$BR_DETAIL" ]] && BR_DETAIL="task"

# --- Issue 作成 ---

echo "GitHub Issue を作成中..." >&2

ISSUE_TITLE="[${TASK_SCOPE}] ${TASK_DESC}"

# ラベルが存在しない場合は --label なしで作成（初回はラベル未設定の可能性）
LABEL_ARGS=()
if gh label list --limit 100 2>/dev/null | grep -q "type:${TASK_TYPE}"; then
  LABEL_ARGS+=(--label "type:${TASK_TYPE}")
fi
if gh label list --limit 100 2>/dev/null | grep -q "scope:${TASK_SCOPE}"; then
  LABEL_ARGS+=(--label "scope:${TASK_SCOPE}")
fi

ISSUE_URL="$(gh issue create \
  --title "${ISSUE_TITLE}" \
  "${LABEL_ARGS[@]}" \
  --body "## 概要

${TASK_DESC}

## タスク種別

- Type: \`${TASK_TYPE}\`
- Scope: \`${TASK_SCOPE}\`

---
*Created via gh-task.sh*" 2>/dev/null)"

# Issue 番号を URL から抽出
ISSUE_NUM="$(echo "$ISSUE_URL" | grep -o '[0-9]\+$')"

if [[ -z "$ISSUE_NUM" ]]; then
  echo "エラー: Issue 番号の取得に失敗しました" >&2
  echo "レスポンス: ${ISSUE_URL}" >&2
  exit 1
fi

# 4桁ゼロパディング
PADDED_NUM="$(printf '%04d' "$ISSUE_NUM")"

# --- ブランチ作成 ---

BRANCH_NAME="LM${PADDED_NUM}-${TASK_TYPE}/${TASK_SCOPE}-${BR_DETAIL}"

echo "ブランチを作成中: ${BRANCH_NAME}" >&2

if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "エラー: ブランチ '${BRANCH_NAME}' は既に存在します" >&2
  exit 1
fi

# ベースブランチに切り替えて最新化
if git show-ref --verify --quiet "refs/heads/${GIT_BASE_BRANCH}"; then
  git checkout "${GIT_BASE_BRANCH}"
  git pull origin "${GIT_BASE_BRANCH}" 2>/dev/null || true
else
  echo "警告: ${GIT_BASE_BRANCH} ブランチが存在しません。現在のブランチから分岐します。" >&2
fi

git checkout -b "${BRANCH_NAME}"

# --- 完了 ---

echo "" >&2
echo "=== タスク作成完了 ===" >&2
echo "  Issue     : #${ISSUE_NUM} - ${ISSUE_TITLE}" >&2
echo "  URL       : ${ISSUE_URL}" >&2
echo "  Branch    : ${BRANCH_NAME}" >&2
echo "  Base      : ${GIT_BASE_BRANCH}" >&2
echo "" >&2
echo "PR 作成時に 'Closes #${ISSUE_NUM}' を含めてください" >&2
