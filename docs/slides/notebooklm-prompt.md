# NotebookLM Slide Generation Prompt

> このファイルの内容をそのまま nano-banana（NotebookLM）に貼り付けてください。

---

ソース資料（presentation-mindmap.md）をもとに、プレゼンテーションスライドを作成してください。

### 対象・目的
- **対象**: Prodapt VP-level executives（technical background, unfamiliar with assignment details）
- **目的**: FDE Capstone final panel presentation — demonstrate architectural thinking, engineering discipline, and value delivered beyond requirements

### スライド仕様
- **枚数**: 最大 22 枚（Demo slide 1枚含む）
- **ブランドカラー**:
  - Primary teal: #2A9D8F
  - Accent blue: #3B82F6
  - グラデーション: teal-400 → teal-500 → blue-500（左→右）
  - テキスト: #0f172a（slate-900）
- **フォント**: Outfit（見出し・ロゴ）、本文はサンセリフ系
- **ロゴ**: `logo-gradient.png` を**全スライドの右上**に配置。灯台アイコン + "Lumineer" テキスト横組み
- **背景**: `slide-background.png`（ライト版）を全スライドの背景として使用
- **言語**: すべて英語

### 構成

| # | タイトル | Key Message | 備考 |
|---|---------|-------------|------|
| 1 | **Title** | "Lumineer — Intelligent Course Discovery System" | 発表者: **Ryota Nakamura** / 日付: **2026/03/18** / GitHub: https://github.com/nakamu12/lumineer を右下に必ず掲載 |
| 2 | **Agenda** | Overview of the presentation flow | Background → Persona → System → Tech → RAG → Validation → Demo → Engineering → Closing。各項目に時間配分を添える |
| 3 | **The Assignment** | "Build an AI-powered course discovery system using 6,645 Coursera courses" | 課題の一文 + Req1/Req2 の2段階要件 |
| 4 | **The Problem** | "6,645 courses. You don't know what you don't know." | 3つの問題を視覚的に整理。引用 "What you don't know is exactly what you need to learn." を強調 |
| 5 | **Requirements → Lumineer** | "We didn't just fulfill requirements. We explained every decision." | 要件対応表（Assignment description / Lumineer implementation / What we went beyond）。ADR 13本に言及 |
| 6 | **Persona: Sarah & Kenji** | "Two different problems. One discovery engine." | Sarah（career changer, skill gap analysis, Web UI）とKenji（enterprise engineer, daily AI tool user）を並列表示。Kenjiの真の課題は後で回収する伏線を示す |
| 7 | **What We Built** | "4-layer architecture. $6/month. Production-grade." | Frontend → Gateway → Backend → AI Processing → Qdrant/OpenAI のシステム全体図。月額コストを添える |
| 8 | **Tech Stack** | "Every choice has a reason. Every reason is documented." | 技術選定表。LangChain棄却・Qdrant採用・text-embedding-3-large選定の判断ロジックを凝縮 |
| 9 | **Clean Architecture** | "Change the LLM provider. Touch one file." | 依存方向図（interfaces/ → usecases/ → ports/ ← infrastructure/）。Port/Adapter による差し替え可能性を強調 |
| 10 | **Authentication** | "JWT. 15-min access token. 7-day refresh. Zero plaintext." | JWT 2トークン設計の概要図。bcrypt・Gateway での検証フロー |
| 11 | **RAG Pipeline** | "6 steps from query to context. Every step is replaceable." | 6ステップフロー図。Strategy パターンで各ステップが切替可能であることを示す |
| 12 | **TOON Format** | "Same budget. 2x more context." | JSON vs TOON のトークン比較図。ヘッダー1行で繰り返しキーを排除する仕組みを視覚化 |
| 13 | **Triage Agent Pattern** | "One entry point. Three specialists. Zero overlap." | 4エージェント構成図（Triage → Search / Skill Gap / Path）。Explore と Chat が同じ Triage Agent を共有することを示す |
| 14 | **5-Layer Guardrails** | "The course added a 4th layer. We added a 5th." | L1〜L5 の表。L5 Economic（独自追加）を強調。並列実行デコレータに触れる |
| 15 | **Observability** | "We don't just run it. We understand why it ran that way." | Langfuse + Prometheus + Grafana の3層構成 |
| 16 | **Validation** | "Quality gates are automated. Not optional." | 3層テスト構成（Unit / RAG Eval / Agent Eval）。CI ゲートを強調 |
| 17 | **[DEMO]** | "Live Demo" | **シンプルに "Live Demo" とだけ表示。スクリーンショット不要。** GitHub URL + QR コードを添える |
| 18 | **AI-Governed Development** | "15 rules. Every commit reviewed by AI. Zero exceptions." | CLAUDE.md + 15 ルールファイル。TDD → Code Review + Security Review（並列）→ PR のフロー |
| 19 | **GitHub-Driven Development** | "Solo project. Team-grade discipline." | 37 PRs / 43 Issues / 4-layer CI / 97% PR-driven を大きく表示。GitHub URL を再掲 |
| 20 | **Spec Deviation → MCP** | "The requirement said 'web app'. The persona needed more." | Kenjiの伏線回収。5ステップの判断プロセス。"MCP Client → Triage Agent → RAG" の図 |
| 21 | **By the Numbers** | "Everything I learned is in this system." | 6,645 courses / 4 agents / 5-layer guardrails / 13 ADRs / 37 PRs / $6/month / ~50% token savings。GitHub URL（https://github.com/nakamu12/lumineer）を大きく掲載 |
| 22 | **Thank You / Q&A** | "Thank you. Questions welcome." | 発表者名 **Ryota Nakamura** / GitHub URL / シンプルな締め |

### トーン・スタイル
- 「なぜこの設計判断をしたか」のトレードオフを明確に伝える
- アーキテクチャ図・技術選定の比較表・データフローを積極的に活用する
- スクリーンショットが必要な箇所は `[SCREENSHOT PLACEHOLDER]` とラベルされたグレーの枠を挿入する（実際の画像はプレゼンター側で差し替える）
- 1スライドにつき要点は3〜5点に絞り、審査員が5秒で把握できるレベルにする
- すべてのテキストは英語で記述する
- GitHub URL（https://github.com/nakamu12/lumineer）は Slide 1・17・19・21・22 に必ず掲載する
