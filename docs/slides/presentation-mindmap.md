# Lumineer — キャプストーン発表 構成マインドマップ

> 15 分 / 約 17 スライド
> 対象：Prodapt VP レベル（技術系エグゼクティブ）
> 評価：35 項目 8 カテゴリ

---

## ナラティブの流れ

```
なぜ作ったか → 誰のために → 何を作ったか → どう作ったか → 見せる → こだわり → 感謝
 (Problem)     (Persona)   (Architecture)  (Tech/RAG)    (Demo)   (Excellence) (Closing)
```

---

## 0. オープニング：Lumineer（ルミニア）とは

- **名前の意味**
  - "Luminate"（照らす）+ "Engineer"（エンジニア）の造語
  - 「学びの道を照らすエンジニアリング」を込めた

- **ブランドカラー**
  - Teal → Blue のグラデーション
  - Teal：「知性・信頼・深さ」を感じさせる色
  - Blue：「可能性・探求・技術」を感じさせる色

- **ロゴ**
  - 灯台 × 本のページを融合したデザイン
  - 「知識で道を照らす」を視覚化

---

## 0.5 Assignment Overview：課題の概要

> ※ VP レベルの審査員は課題詳細を事前に見ていない前提で、冒頭に簡潔に説明する

**与えられた課題（一言）：**
> "Coursera の 6,645 件のコースデータを使って、AI エージェントによるインテリジェントなコース発見システムを作れ"

**課題が定義していた問題：**
- 大学・社会人が学習コースを探す際、キーワード検索では「自分が何を学ぶべきか」が分からない
- 前提知識のギャップ・学習パス・キャリアとの接続が見えない
- 課題の要件書には Req1（Basic）と Req2（Advanced）の2段階が設定されていた

**要件と Lumineer の実装対応：**

| 要件カテゴリ | 課題の記述 | Lumineer の実装 | 超えた点 |
|------------|-----------|----------------|---------|
| 検索 | Basic RAG + セマンティック検索 | Hybrid RAG（Dense + Sparse + RRF）+ TOON | トークン最適化まで独自設計 |
| エージェント | 5エージェント構成 | Triage + 3専門エージェント（構造を最適化） | Triage パターンで拡張性を確保 |
| ガードレール | 学習目標バリデーション（基本） | 5層防衛アーキテクチャ（L5 Economic 独自追加） | 授業の4層を1層拡張 |
| 評価 | DeepEval + LLM-as-Judge | DeepEval + Golden Dataset（CI ゲート化） | 品質ゲートを自動化・CI に組み込み |
| UI | "シンプルなフロントエンド" | プロダクト品質 UI + ブランドデザイン | 「シンプル」を超えたプロダクト化 |
| インフラ | API エンドポイント公開 | 4レイヤーアーキテクチャ + API Gateway | マイクロサービス要件も満たす設計 |
| ―（要件外） | 記述なし | MCP Server | ペルソナ起点の要件外価値提供 |

**語り方：**
- 「与えられた要件をそのまま実装した」ではなく、「**要件を出発点として、なぜそう設計したかを全て説明できる形**で作った」
- 各判断は ADR（13本）として記録済み

---

## 1. Problem：なぜ作ったか

- **量の問題**
  - Coursera に 6,645 コースある
  - 多すぎて「どれが自分に合うか」がわからない

- **検索の限界**
  - キーワード検索は「知っている言葉」でしか探せない
  - 「自分が何を知らないか」はわからない

- **構造化された学習支援がない**
  - スキルギャップを分析してくれる機能がない
  - 目標から逆算した学習パスを作ってくれる機能がない

- **一言でまとめると：**
  > "What you don't know is exactly what you need to learn."

---

## 2. Persona：誰のために作ったか

- **Sarah（28歳・キャリアチェンジャー）← Primary**
  - 背景：マーケターからデータサイエンティストへの転職志望
  - 課題：「何のスキルが足りないか」がわからない
  - ニーズ：スキルギャップ分析 + 学習パス生成
  - 使い方：Web UI（Chat・Explore）

- **Kenji（35歳・日本の大企業エンジニア）← Secondary**
  - 背景：大手製造業のシステムエンジニア。社内デジタル化推進チームに所属
  - 日常：業務で AI ツールを積極的に活用しており、技術的な情報収集は得意
  - 表面的な課題：
    - キャリアアップのためにコースを探しているが「今の自分に何が必要か」が整理できていない
    - 新しい外部サービスを使うには IT 部門への申請と承認フローが必要で、試すまでに時間がかかる
    - Coursera を漠然と眺めることはあるが、決め手に欠けてそのまま閉じてしまう
  - 伏線となる行動パターン：
    - **日常的に AI ツールで業務の問いかけをすることには慣れている**
    - 「調べ物は AI に聞く」が自然な習慣になっている
  - 本人も気づいていない真の課題：← **Engineering Excellence セクションで回収**

- **設計のポイント**
  - 2 人の課題は異なるが、同じ「コース発見エンジン」で解決できる
  - Sarah は「何が足りないか知りたい」、Kenji は「どこからでも使いたい」← デモ後に深掘りする

---

## 3. What I Built：全体像

- **Lumineer の全体構成**
  - `Frontend → Gateway → Backend → AI Processing → Qdrant / OpenAI`
  - 月額インフラコスト：約 $6

```
Frontend (React+Vite)
    ↓
Gateway (Hono)          ← 唯一の外部公開エントリポイント
    ↓
Backend (Hono)          ← Clean Architecture / 内部のみ
    ↓
AI Processing (Python)  ← Agents SDK + RAG / 内部のみ
    ↓
Qdrant / OpenAI
```

---

## 4. Tech Stack：技術選定

| レイヤー | 技術 | 選んだ理由 |
|---------|------|-----------|
| Frontend | React + Vite + Shadcn UI | Bun 統一で型共有。Shadcn でプロダクト品質を最速で |
| Gateway | Hono (TypeScript) | 薄いルーティング層。ビジネスロジックを持たない |
| Backend | Hono + Clean Architecture | Port/Adapter で外部依存を抽象化。OpenAI → Claude はアダプタ変更のみ |
| AI Processing | Python + Litestar | AI エコシステムが Python に集中（Agents SDK, DeepEval, Qdrant client） |
| Agent Framework | OpenAI Agents SDK | RAG の中身を理解して実装するため（LangChain は棄却） |
| VectorDB | Qdrant | Hybrid Search ネイティブ対応（ChromaDB は Sparse Vector 非対応で棄却） |
| Embedding | text-embedding-3-large | 対象 6,645 件と小規模。large と small のコスト差は $0.22。精度を妥協する理由がない |
| RDB | PostgreSQL + Drizzle ORM | アプリデータ管理。SQL に近い記法 × 型安全 |
| LLM | GPT-4o-mini | コスト・速度・精度のバランス |

**こだわりポイント（積極的にアピール）**
- LangChain 棄却：「RAG の内部を理解していることを示したかった」
- Qdrant 採用：「Hybrid Search がネイティブ対応。自前実装不要」
- Modular Monolith（ADR-001）：「1人開発でマイクロサービスは Anti-pattern。ただしモジュール境界は明確で将来の分離が容易」
- **Embedding モデル選定（Model Selection）**：
  - 対象データは 6,645 件と小規模。再 Embedding が必要になっても数分 + 数十セントで完了
  - small と large のコスト差はわずか $0.22（一回きり）
  - MTEB 精度：large 64.6% vs small 62.3%
  - 「スケールが小さいからこそ、コストを気にせず最高精度のモデルを選べる」← SMB の強み

---

## 5. Architecture：各レイヤーの構成

### Frontend
- React + Vite + Shadcn UI + Tailwind CSS
- Feature-based 構成（search / chat / path / explore / auth / settings）
- Vite proxy → Gateway 経由で API 呼び出し

### Gateway
- Hono（TypeScript）
- 責務：CORS・ログ・レート制限・proxy のみ
- ビジネスロジックは一切持たない薄い層

### Backend（Clean Architecture） ← アピールポイント
- 構造：`interfaces/ → usecases/ → ports/ ← infrastructure/`
- Domain 層は外部依存ゼロ
- LLM・VectorDB・Embedding を Port で抽象化
- 「OpenAI → Claude への切り替えはアダプタ 1 つの変更のみ」
- ORM：Drizzle ORM

**認証（Auth integration）**
- JWT（jose）+ bcrypt で実装
- Access Token（15分）+ Refresh Token（7日）の 2 トークン設計
- Gateway から Backend への転送時に JWT 検証を必須化
  - `Authorization: Bearer <token>` ヘッダーを Hono Middleware で検証
  - 検証失敗時は 401 を返し、Backend 内部には到達させない
- パスワードは bcrypt（cost factor 12）でハッシュ化。平文保存禁止

### AI Processing
- Python + Litestar
- 構造：agents / tools / prompts / guardrails / domain / infrastructure
- プロンプトは `prompts/*.md` に外部化（コード変更なしで調整可能）

### Database
- PostgreSQL：アプリデータ（ユーザー・チャット・学習パス・設定）
- Qdrant：ベクトル検索（6,645 コースの埋め込み）
- 役割分担を明確に分離

---

## 6. RAG Pipeline & Guardrails

### Ingestion（データ取り込み）
- CSV → GPT-4o-mini 前処理（Skills 欠損 29% を補完）→ Embedding → Qdrant
- コスト：$1.36（一回きり）

### 検索パイプライン（6 ステップ）
1. メタデータフィルタ（Level / Organization / rating など）
2. Dense + Sparse 並列検索（意味検索 × キーワードマッチ）
3. RRF スコア統合（順位ベース・正規化不要）
4. Reranking（Strategy パターン：none / heuristic / cross-encoder）
5. Result Selection（Top-k + Threshold）→ 不足時は Corrective RAG
6. Context Assembly（JSON or **TOON**）

### TOON（独自コスト最適化） ← 差別化ポイント
- JSON はフィールド名が件数分繰り返される（10件 × 6フィールド = 60 重複キー）
- TOON はヘッダー 1 行のみ → トークン約 50% 削減
- 同じ予算でより多くの検索結果をコンテキストに入れられる
- Strategy パターンで切替可能（Settings UI でデモ中にトグル）

### Agents（Triage パターン）
- 授業通りの Triage パターン + 4 エージェント
- Triage → Search / Skill Gap / Path に handoff
- 各エージェントは最小権限の Tool のみ
- Explore と Chat は同じ Triage Agent を使用（出力フォーマットのみ違う）

### 5 層ガードレール ← 「授業の 4 層に L5 Economic を独自追加」
- L1 Input：インジェクション・Toxicity・Off-topic・PII マスキング
- L2 Data：Context Window 保護・RAG データ検証
- L3 Agent：Tool 権限・Persona Lock・ループ検出
- L4 Output：ハルシネーション検出（DB 照合 $0 + LLM Verifier 並列）
- L5 Economic：トークン制限・レート制限・コスト追跡 ← **独自拡張**
- 全ガードレールは `@input_guardrail` / `@output_guardrail` デコレータで並列実行

### モニタリング & デバッグ（Observability）
- **Langfuse** でエージェントの全実行をトレーシング
  - プロンプト入出力・トークン消費・レイテンシをリクエスト単位で記録
  - どのガードレールが発動したか、どのエージェントに handoff したかを可視化
  - 「何かおかしい」と思ったとき、Langfuse を見れば原因が分かる設計
- **Prometheus + Grafana** でインフラメトリクスを監視
  - API レスポンスタイム・エラー率・Qdrant 検索レイテンシ
- 「動いているだけ」ではなく「**なぜそう動いたかを説明できる**」構成

---

## 7. Validation：品質保証

### Layer 1：Unit Test
- Vitest（Frontend / Backend）+ pytest（AI Processing）
- 29 ファイル。毎コミット実行

### Layer 2：RAG Evaluation
- DeepEval + Golden Dataset（80〜100 件）
- CI ゲート：Hit Rate・Hallucination・Faithfulness が閾値未満ならマージブロック

### Layer 3：Agent Evaluation
- LLM-as-Judge
- 4 エージェントの統合品質テスト
- リリース前・手動実行

---

## 8. Live Demo（デモ）

実際のアプリを動かして見せる。**デモ中はなるべく話さない。動きで見せる。**

| ステップ | 時間 | 見せるもの |
|---------|------|-----------|
| Home | 0:15 | ブランド・LP |
| Explore - 検索 | 0:45 | "machine learning beginners"、フィルタ、AI 結果 |
| Course Detail | 0:15 | カードクリック、詳細ページ |
| Login | 0:15 | JWT 認証 |
| Chat - 検索 | 0:30 | "Python courses for data science"、SSE ストリーミング |
| Chat - スキルギャップ | 0:30 | "I know Python and SQL, what do I need for DS?" |
| Chat - 学習パス | 0:30 | "3-month plan for data science" |
| Settings | 0:15 | Reranker / TOON トグル |

---

## 9. Engineering Excellence：こだわりの開発手法

### AI 駆動開発（AI-Governed Development）
- CLAUDE.md + 15 ルールファイルで AI の行動を制約
- フロー：TDD → Code Review + Security Review（並列 AI サブエージェント）→ PR
- 「AI にコードを書かせた」ではなく「**AI を 15 のルールで統治した**」
- この開発手法自体が、他のキャプストーンとの明確な差別化

### GitHub-Driven Development
- 37 PR マージ / 43 Issue / 4-layer CI / 97% PR 駆動
- git worktree で並行開発（develop への直接コミット 0）
- Issue → Kanban 自動連携 → PR マージで自動クローズ
- 1人プロジェクト、チームグレードの規律

### ブランディング ← おそらく自分だけ
- 名前の選定：Lumineer（意味を持って命名）
- ロゴ：灯台 × 本のページ
- カラー：Teal → Blue グラデーション（色の意味も設計）
- UI・スライド・favicon まで一貫したブランド体験
- 「プロダクトとして完結させた」という意識

### 仕様の乖離と顧客の真意（Ambiguity handling）
- キャプストーン要件には「Web アプリケーション」と記載されていた
- しかしペルソナ設計を深掘りする中で「**本当に必要なのは Web アプリだけではない**」という気づきがあった
  - Kenji のような「既存ツールに組み込みたい」ニーズは、Web UI では解決できない
  - 要件の文字通りではなく、**顧客が達成したいゴール**を起点に設計を判断した
- この判断プロセス：
  1. ペルソナの「行動パターン」を観察 → AI ツールを日常的に使っている
  2. 「なぜ Coursera は AI から呼べないのか？」という問いが生まれた
  3. MCP という解決策が、Clean Architecture の設計上 **ゼロコストで追加可能**と判断
  4. 要件を超えた価値提供として MCP を設計・実装方針を決定
- 「要件に忠実に作る」よりも「**顧客の真の課題を解く**」を優先した判断

### MCP（Kenji の真の課題を回収） ← ここで伏線を回収する

**語りの構造：**
1. 「Kenji を覚えていますか？」と問いかける
2. 「彼は毎日 AI ツールで業務の問いかけをしていた」と補足
3. 「では、なぜコース検索だけ別のサービスを使わなければならないのか？」← 真の課題の提示
4. 「Kenji が本当に欲しかったのは、新しいサービスではなく、使い慣れた AI から答えが得られること」← 気づき
5. MCP がその答えである、と結論づける

**MCP が解決すること：**
- 使い慣れた AI ツール（MCP 対応クライアント）から Lumineer のコース知識にアクセスできる
- RAG パイプライン（ベクトル検索・コース知識）はサーバー側で完結
- LLM 推論はクライアント側（使い慣れた AI）で行われる
- 新しいサービス登録・承認フロー・追加コストが一切不要

**Clean Architecture だから実現できた：**
- Web UI と MCP は同じ Triage Agent + RAG を共有
- インターフェース（入口）を追加するだけ。ドメインロジックは一切変更しない

```
Web UI -------> Triage Agent ---> RAG ---> Response
                     ^
MCP Client ----/
(使い慣れた AI ツール)

RAG: サーバー側（Lumineer が提供）
LLM: クライアント側（Kenji が日常使いしている AI）
新規登録: 不要   承認フロー: 不要   追加コスト: $0
```

---

## 10. Closing：まとめと感謝

### 数字でまとめ

```
6,645 courses | 4 agents | 5-layer guardrails | 13 ADRs
37 PRs | 29 test files | 4-layer CI | 15 AI rule files
$6/month infra | $1.36 data cost | ~50% token savings (TOON)
```

### キャリアについて
- このプログラムを通じて、フルスタックエンジニア（FSD）を本気で目指すきっかけになった
- フロントエンドからバックエンド、AI パイプライン、インフラまで、エンドツーエンドで設計・実装できる実感を得た

### 感謝
- このプログラムで学んだことがすべて Lumineer に詰まっている
- 審査員・メンター・チームへの感謝を伝える

---

## 想定 Q&A

| 質問 | 回答 |
|------|------|
| なぜ LangChain を使わなかったか？ | RAG の内部を理解していることを示したかったため。LangChain は中身を隠す |
| なぜ Qdrant か？ | Hybrid Search のネイティブ対応。ChromaDB は Sparse Vector 非対応 |
| なぜ 4 レイヤーか？ | キャプストーン要件の「API Gateway」を満たしつつ、責務を明確に分離するため |
| ハルシネーション対策は？ | 2 段構成：DB 照合（コスト $0）+ LLM Verifier（並列 @output_guardrail） |
| インフラコストは？ | $6/月。Cloud Run 無料枠 + Qdrant Cloud 無料枠の組み合わせ |
| MCP は実装済みか？ | ADR-012-11 で設計済み。Clean Architecture によりインターフェース追加のみで対応可能 |
| なぜ text-embedding-3-large か？ | 対象 6,645 件と小規模。small との精度差 2.3%、コスト差 $0.22。精度を妥協する理由がない |
| エージェントのデバッグはどうするか？ | Langfuse でプロンプト入出力・トークン消費・ガードレール発動を全トレース。原因箇所を即座に特定できる |

---

## タイミング概要

> ⚠️ **時間注意**: 課題PDF では発表8分+Q&A2分＝計10分と記載。実際の持ち時間を要確認。
> 現在の構成は15分想定。10分の場合はTech Stack・Validationを圧縮し、Architectureをまとめる必要あり。

**15分構成（現在）：**

| # | セクション | 時間 | 累計 |
|---|-----------|------|------|
| 0 | オープニング（Lumineer 紹介） | 0:20 | 0:00-0:20 |
| 0.5 | Assignment Overview（課題の概要） | 0:30 | 0:20-0:50 |
| 1 | Problem | 0:30 | 0:50-1:20 |
| 2 | Persona | 0:40 | 1:20-2:00 |
| 3 | What I Built（全体像） | 0:30 | 2:00-2:30 |
| 4 | Tech Stack | 0:45 | 2:30-3:15 |
| 5 | Architecture | 1:15 | 3:15-4:30 |
| 6 | RAG Pipeline & Guardrails | 2:00 | 4:30-6:30 |
| 7 | Validation | 0:30 | 6:30-7:00 |
| 8 | Live Demo | 3:30 | 7:00-10:30 |
| 9 | Engineering Excellence | 2:30 | 10:30-13:00 |
| 10 | Closing | 0:30 | 13:00-13:30 |
| | **バッファ** | **1:30** | **13:30-15:00** |

**10分構成（圧縮版・要検討）：**

| # | セクション | 時間 | 累計 |
|---|-----------|------|------|
| 0+0.5 | Opening + Assignment Overview | 0:30 | 0:00-0:30 |
| 1+2 | Problem + Persona | 0:45 | 0:30-1:15 |
| 3+4+5 | Architecture 全体（Tech Stack統合） | 1:15 | 1:15-2:30 |
| 6 | RAG + Guardrails（要点のみ） | 1:00 | 2:30-3:30 |
| 7 | Demo | 3:00 | 3:30-6:30 |
| 8 | Engineering Excellence（要点のみ） | 1:00 | 6:30-7:30 |
| 9 | Closing | 0:30 | 7:30-8:00 |
| | **Q&A** | **2:00** | **8:00-10:00** |
