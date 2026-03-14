#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# gh-branch.sh — 既存 GitHub Issue からブランチ作成
#
# 使い方: gh-branch.sh "<Issue番号>" ["<カスタムブランチ名>"]
# 例:     gh-branch.sh "5" "hybrid-search"
#         gh-branch.sh "LM0005"
#
# omnicore-app の notion-branch.sh に相当する GitHub 版。
# =============================================================================

RAW_INPUT="${1:?Issue 番号を指定してください（例: 5, LM0005, #5）}"
CUSTOM_SUFFIX="${2:-}"

GIT_BASE_BRANCH="${GIT_BASE_BRANCH:-develop}"

# --- Issue 番号のパース ---

# LM0005, #5, 5 いずれの形式でも受け付ける
ISSUE_NUM="$(echo "$RAW_INPUT" | sed -E 's/^(LM|lm|CF|cf|#)0*//' | grep -o '[0-9]\+' || true)"

if [[ -z "$ISSUE_NUM" ]]; then
  echo "エラー: Issue 番号を解析できませんでした: ${RAW_INPUT}" >&2
  echo "  許可形式: 5, #5, LM0005" >&2
  exit 2
fi

# --- gh CLI チェック ---

if ! command -v gh &>/dev/null; then
  echo "エラー: gh CLI がインストールされていません" >&2
  exit 1
fi

# --- Git 状態チェック ---

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "エラー: 未コミットの変更があります。先にコミットしてください。" >&2
  git status --porcelain >&2
  exit 1
fi

# --- Issue 情報取得 ---

echo "Issue #${ISSUE_NUM} の情報を取得中..." >&2

ISSUE_JSON="$(gh issue view "$ISSUE_NUM" --json title,labels,state 2>/dev/null)" || {
  echo "エラー: Issue #${ISSUE_NUM} が見つかりません" >&2
  exit 1
}

ISSUE_TITLE="$(echo "$ISSUE_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['title'])")"
ISSUE_STATE="$(echo "$ISSUE_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['state'])")"

if [[ "$ISSUE_STATE" == "CLOSED" ]]; then
  echo "警告: Issue #${ISSUE_NUM} はクローズ済みです" >&2
fi

# ラベルから type と scope を抽出
TASK_TYPE="$(echo "$ISSUE_JSON" | python3 -c "
import json,sys
labels = json.load(sys.stdin).get('labels', [])
for l in labels:
    name = l.get('name', '')
    if name.startswith('type:'):
        print(name.split(':',1)[1])
        break
else:
    print('feature')
" 2>/dev/null)"

TASK_SCOPE="$(echo "$ISSUE_JSON" | python3 -c "
import json,sys
labels = json.load(sys.stdin).get('labels', [])
for l in labels:
    name = l.get('name', '')
    if name.startswith('scope:'):
        print(name.split(':',1)[1])
        break
else:
    print('backend')
" 2>/dev/null)"

# --- ブランチ名生成 ---

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/\[.*\]//g' \
    | sed -E 's/[[:space:]]+/-/g' \
    | sed -E 's/[^a-z0-9_-]+//g' \
    | sed -E 's/^-+//; s/-+$//' \
    | cut -c1-48
}

if [[ -n "$CUSTOM_SUFFIX" ]]; then
  BR_DETAIL="$(slugify "$CUSTOM_SUFFIX")"
else
  BR_DETAIL="$(slugify "$ISSUE_TITLE")"
fi
[[ -z "$BR_DETAIL" ]] && BR_DETAIL="task"

PADDED_NUM="$(printf '%04d' "$ISSUE_NUM")"
BRANCH_NAME="LM${PADDED_NUM}-${TASK_TYPE}/${TASK_SCOPE}-${BR_DETAIL}"

# --- ブランチ作成 ---

echo "ブランチを作成中: ${BRANCH_NAME}" >&2

if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "エラー: ブランチ '${BRANCH_NAME}' は既に存在します" >&2
  exit 1
fi

if git show-ref --verify --quiet "refs/heads/${GIT_BASE_BRANCH}"; then
  git checkout "${GIT_BASE_BRANCH}"
  git pull origin "${GIT_BASE_BRANCH}" 2>/dev/null || true
else
  echo "警告: ${GIT_BASE_BRANCH} ブランチが存在しません。現在のブランチから分岐します。" >&2
fi

git checkout -b "${BRANCH_NAME}"

# --- 完了 ---

echo "" >&2
echo "=== ブランチ作成完了 ===" >&2
echo "  Issue     : #${ISSUE_NUM} - ${ISSUE_TITLE}" >&2
echo "  Type      : ${TASK_TYPE}" >&2
echo "  Scope     : ${TASK_SCOPE}" >&2
echo "  Branch    : ${BRANCH_NAME}" >&2
echo "  Base      : ${GIT_BASE_BRANCH}" >&2
