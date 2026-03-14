#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# gh-labels.sh — GitHub リポジトリにラベルを一括作成
#
# リポジトリ作成後に一度だけ実行する初期化スクリプト。
# 使い方: bash scripts/gh-labels.sh
# =============================================================================

if ! command -v gh &>/dev/null; then
  echo "エラー: gh CLI がインストールされていません" >&2
  exit 1
fi

echo "=== Type ラベル作成 ===" >&2

# Type ラベル
gh label create "type:feature"  --color 0E8A16 --description "新機能"           --force 2>/dev/null || true
gh label create "type:fix"      --color D93F0B --description "バグ修正"         --force 2>/dev/null || true
gh label create "type:hotfix"   --color B60205 --description "緊急修正"         --force 2>/dev/null || true
gh label create "type:refactor" --color FBCA04 --description "リファクタリング" --force 2>/dev/null || true
gh label create "type:docs"     --color 0075CA --description "ドキュメント"     --force 2>/dev/null || true
gh label create "type:test"     --color BFD4F2 --description "テスト"           --force 2>/dev/null || true
gh label create "type:chore"    --color D4C5F9 --description "雑務・設定"       --force 2>/dev/null || true

echo "=== Scope ラベル作成 ===" >&2

# Scope ラベル
gh label create "scope:frontend" --color 1D76DB --description "Frontend (React)" --force 2>/dev/null || true
gh label create "scope:backend"  --color 5319E7 --description "API Layer (Hono)" --force 2>/dev/null || true
gh label create "scope:rag"      --color 006B75 --description "RAG パイプライン" --force 2>/dev/null || true
gh label create "scope:agents"   --color E99695 --description "AI エージェント"  --force 2>/dev/null || true
gh label create "scope:data"     --color F9D0C4 --description "データ処理"       --force 2>/dev/null || true
gh label create "scope:infra"    --color C2E0C6 --description "インフラ・CI/CD"  --force 2>/dev/null || true
gh label create "scope:mcp"      --color D876E3 --description "MCP Server"       --force 2>/dev/null || true

echo "=== Priority ラベル作成 ===" >&2

# Priority ラベル
gh label create "priority:must"   --color B60205 --description "Must Have"   --force 2>/dev/null || true
gh label create "priority:should" --color FF9F1C --description "Should Have" --force 2>/dev/null || true
gh label create "priority:could"  --color FEF2C0 --description "Could Have"  --force 2>/dev/null || true

echo "" >&2
echo "=== ラベル作成完了 ===" >&2
gh label list >&2
