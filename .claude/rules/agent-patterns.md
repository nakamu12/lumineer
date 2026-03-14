---
description: OpenAI Agents SDK のエージェント設計パターン
globs: ai/app/agents/**
---

# Agent Pattern Rules

## Triage パターン（4 エージェント）

```
              ┌─────────────┐
ユーザー入力 → │ Triage Agent │ ← 分類・ルーティング
              └──────┬──────┘
                     │ handoff()
        ┌────────────┼────────────┐
        ▼            ▼            ▼
 Search Agent   Skill Gap    Path Agent
 コース検索     スキル分析    学習パス
```

## Agent 定義の構造

```python
# ✅ Agent はルーティングと instructions のみ
triage_agent = Agent(
    name="Triage Agent",
    instructions=open("app/prompts/triage.md").read(),  # 外部ファイル
    handoffs=[search_agent, skill_gap_agent, path_agent],
)

# ❌ instructions にロジックを書かない
triage_agent = Agent(
    instructions="ユーザーの入力を解析し、..."  # ハードコード
)
```

## Handoff 規約

- Triage Agent → 専門 Agent への一方向 handoff
- 専門 Agent 同士は直接 handoff しない（Triage に戻す）
- ループ検出: ターン数上限 + handoff 回数制限を設定

## Tool Permission Scoping

- 各 Agent は必要最小限の Tool のみ持つ
- Search Agent: `search_courses`, `get_course_detail`
- Skill Gap Agent: `analyze_skill_gap`
- Path Agent: `generate_learning_path`
- Triage Agent: Tool なし（ルーティングのみ）

## 統一バックエンド

- Explore 検索バーと Chat 画面は同じ Triage Agent を呼ぶ
- 違いは出力フォーマットのみ:
  - Explore: AI 要約 + カードグリッド
  - Chat: 会話形式 + インラインカード

## Persona Lock

- 各 Agent の instructions に役割制約を明記
- 例: Search Agent は「医療アドバイス」「投資助言」をしない
- 出力ガードレールで逸脱を検証
