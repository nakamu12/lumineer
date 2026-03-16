# Architecture Decision Records (ADR)

> Lumineer – Intelligent Course Discovery System
> キャプストーンプロジェクトのアーキテクチャ判断記録

---

## ADR-001: システム境界 — モジュラーモノリス

### Status: Accepted

### Context
仕様書の成果物3に「Full Executable Code (Microservice)」と記載されている。しかしプロジェクトは1人開発、デモ用途であり、マイクロサービスの恩恵（独立スケール、独立デプロイ、チーム分離）を享受する条件が揃っていない。

### Decision
**モジュラーモノリス** + Docker Compose を採用する。

- 内部をモジュール（ingestion, search, recommendation, agents）に明確に分割
- Docker Composeでパッケージング（app + vectordb + frontend の構成）
- モジュール間は関数呼び出し（プロセス内通信）

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **マイクロサービス** | 1人開発でサービス分割の恩恵がない。分散トランザクション・サービス間通信の複雑さが開発速度を下げる。Anti-pattern「分散モノリス」のリスク |
| **モノリス（分割なし）** | 内部構造が曖昧になり、将来の拡張が困難。設計判断力を示せない |
| **Kubernetes** | 3-4コンテナの管理にK8sはオーバーキル。Docker Composeで十分 |

### Consequences
- ✓ 開発速度を維持しつつ、内部の責務分離を実現
- ✓ 設計ドキュメントで「なぜマイクロサービスにしなかったか」をトレードオフとして説明可能
- ✓ 将来のマイクロサービス化が容易（モジュール境界が明確）
- ✗ 仕様書の「Microservice」文言との整合性はヒアリングで確認が必要

---

## ADR-002: バックエンド構造 — クリーンアーキテクチャ

### Status: Accepted

### Context
AI/LLMシステムでは外部依存（LLMプロバイダー、VectorDB、埋め込みモデル）が多く、これらは変更される可能性が高い。ビジネスロジック（コース検索、スキルギャップ分析、学習パス生成）を外部変更から保護する設計が必要。

### Decision
**クリーンアーキテクチャ**を採用する。

```
app/
├── domain/                 # ★核心（外部に一切依存しない）
│   ├── entities/           #   Course, LearningPath, SkillGap
│   ├── ports/              #   LLMPort, VectorStorePort, EmbeddingPort
│   └── usecases/           #   search_courses, analyze_skill_gap,
│                           #   generate_learning_path
├── infrastructure/         # 外部接続の具体実装
│   ├── llm/                #   LLMアダプタ（OpenAI等）
│   ├── vectordb/           #   VectorDBアダプタ
│   ├── embeddings/         #   埋め込みモデルアダプタ
│   └── ingestion/          #   CSVLoader, DataCleaner
├── interfaces/             # 入力アダプタ
│   └── api/                #   API Router
├── agents/                 # エージェント群（usecasesを使うオーケストレーション層）
│   ├── retrieval_agent.py
│   ├── skill_gap_agent.py
│   └── learning_path_agent.py
└── config/                 # DI設定
    └── container.py
```

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **レイヤードアーキテクチャ** | Router→Service→Repositoryの一方通行。シンプルだがInfrastructure層の変更がService層に波及する。LLMプロバイダー切り替え時にビジネスロジックも修正が必要になる |
| **フラット構造** | プロトタイプ向け。キャプストーンの規模と設計アピールに不適 |
| **Hexagonal (ポート&アダプタ)** | クリーンアーキテクチャと本質的に同じ考え方。クリーンアーキの方が参照情報が多い |

### Consequences
- ✓ LLMプロバイダー（OpenAI→Claude→Gemini）の切り替えがconfig変更のみ
- ✓ VectorDB（ChromaDB→Qdrant→Milvus）の移行がアダプタ差し替えのみ
- ✓ Domain層のユニットテストが容易（外部依存なし、モック不要）
- ✓ 設計の成熟度を審査で示せる
- ✗ 初期コストがレイヤードより高い（ポート/アダプタの定義が必要）

---

## ADR-003: API層 — Bun + Hono

### Status: Accepted (FastAPI統一案も候補として保留)

### Context
フロントエンドにBun + React (TypeScript) を採用するため、API層もTypeScriptで統一することでフロント↔バック間の型定義共有が可能になる。AI処理は別プロセス（Python）で動かす前提。

### Decision
**Bun + Hono** をAPI層に採用する。

- Honoはルーティング、認証、リクエストバリデーションを担当
- AI処理はPythonプロセスにHTTPで委譲
- フロントエンドとの型定義共有が可能

### Alternatives Considered

| 選択肢 | 検討状況 |
|--------|---------|
| **FastAPI統一（API層もPython）** | 候補として保留中。1言語で済むメリットがある。ただしフロントとの型共有ができない |
| **Go + gRPC** | 音声入力の誤認識で一時検討。3言語（Go + Python + TypeScript）になり管理負荷が高い |
| **Express.js** | Honoより古く、パフォーマンスで劣る |
| **Node.js** | BunがNode.js互換でより高速。Bunを選ぶ理由がある以上Node.jsを選ぶ理由がない |

### Consequences
- ✓ フロントエンドとTypeScript型定義を共有可能
- ✓ Honoは軽量・高速で、API層に特化した設計
- ✓ Bun統一でフロント・バックの開発体験が統一
- ✗ API層とAI処理層が別言語（TypeScript + Python）→ 2プロセス管理が必要
- ✗ Hono↔Python間の通信設計が必要

---

## ADR-004: AI処理層 — Python + Litestar

### Status: Accepted (FastAPIも候補として保留)

### Context
AI/RAGのエコシステム（Agents SDK, DeepEval, ChromaDB, sentence-transformers等）はPythonに集中しており、他言語での代替が困難。Webフレームワークの選択はLangChainを使わない前提で再評価した。

### Decision
**Python + Litestar** をAI処理層に採用する。

### Alternatives Considered

| 選択肢 | 検討状況 |
|--------|---------|
| **FastAPI** | 候補として保留。コミュニティ・ドキュメントが圧倒的に豊富。LangChainとの連携例も多い。ただし今回LangChainを使わないため、この優位性は薄れる |
| **Bun + Hono統一（JavaScript）** | DeepEvalがPython専用で使えない。LangChain.jsは機能不足。マルチエージェント系ライブラリがJS版で大幅に遅れている。エコシステムの制約から棄却 |
| **Flask** | 非同期非対応。FastAPI/Litestarより機能面で劣る |
| **gRPCサーバー（フレームワークなし）** | Go API層の場合は有力だったが、Hono（HTTP）との連携ならHTTPフレームワークの方が自然 |

### Litestar vs FastAPI の詳細比較

| 観点 | FastAPI | Litestar |
|------|---------|----------|
| 初リリース | 2018年 | 2022年 |
| DIの設計 | `Depends()` で都度指定 | コンストラクタ注入、アプリレベルで一括設定 |
| クリーンアーキとの相性 | 関数ベース、やや工夫が必要 | クラスベースでポート/アダプタと自然に対応 |
| 型安全性 | 良い | より厳密（戻り値もバリデーション） |
| パフォーマンス | 速い | ベンチマークでやや上 |
| コミュニティ | 圧倒的に大きい (80k+ stars) | 小さい (5k stars) |
| LLMライブラリ連携 | 事例豊富 | 自分で組み合わせる必要あり |

Litestarを選んだ主な理由: クリーンアーキテクチャのクラスベースDIとの相性。LangChainを使わないため、FastAPIの連携例の豊富さが決定要因にならない。

### Consequences
- ✓ クラスベースのコントローラーがクリーンアーキテクチャのポート/アダプタと自然に対応
- ✓ 「最新のフレームワークを選定し、理由を説明できる」設計判断力の証明
- ✗ ドキュメント・事例が少ない。困った時の解決に時間がかかるリスク
- ✗ 審査員が知らない可能性がある（説明コスト）

---

## ADR-005: AIオーケストレーション — OpenAI Agents SDK

### Status: Accepted

### Context
マルチエージェント構成が仕様書Req2で求められている。エージェントのオーケストレーション方法として、LangChainとAgents SDKを比較した。

### Decision
**OpenAI Agents SDK** を採用する。RAGパイプラインは自前実装。

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **LangChain** | 抽象化が厚く、デバッグが困難。RAGパイプラインの中身が隠蔽される。キャプストーンで「仕組みを理解している」ことを示すには不向き |
| **LlamaIndex** | RAG特化だが、マルチエージェントのサポートが弱い |
| **LangGraph** | グラフベースのエージェントオーケストレーション。Agents SDKよりAPIが複雑 |

### Consequences
- ✓ エージェント・ツールコール・ハンドオフに特化したシンプルなAPI
- ✓ RAGを自前実装 → パイプラインの仕組みを完全に理解・説明できる
- ✓ LangChainの抽象化に隠されず、デバッグが容易
- ✗ RAGパイプライン（埋め込み→検索→リランキング）を自分で組む工数
- ✗ LLMプロバイダーがOpenAI前提（ただしクリーンアーキのポートで抽象化可能）

---

## ADR-006: フロントエンド技術スタック

### Status: Accepted

### Context
キャプストーンのフロントエンドは「エンドユーザーがサービスとどうやり取りできるかを示すシンプルなUI」（仕様書Req2）。デモ用途であり、UIの作り込みより機能のデモが重要。

### Decision
以下の技術スタックを採用する:
- **ランタイム**: Bun（npm/yarnより高速、TypeScriptネイティブ実行）
- **フレームワーク**: React (Vite)
- **UIコンポーネント**: Shadcn UI（コピペ式、カスタマイズ自由）
- **CSS**: Tailwind CSS（Shadcn UIの必須基盤）
- **アニメーション**: Magic UI / Aceternity UI（候補。デモ映え用。後日決定）

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **npm / yarn** | Bunの方が高速。TypeScriptのネイティブ実行をサポート |
| **Next.js** | SSR/SSGの恩恵がデモ用SPAでは不要。Viteの方が軽量 |
| **MUI (Material UI)** | デザインがGoogle Material Designに固定される。カスタマイズ時にCSS上書きが面倒。バンドルサイズ大 |
| **CSS Modules** | Shadcn UIとの併用が非推奨 |
| **Styled Components** | CSS-in-JS。ランタイムコストがある。トレンドとして下降中 |
| **Panda CSS** | 型安全で新しいが、Shadcn UIが使えなくなる |

### フロントエンド構造: Feature-based + lib/

```
frontend/
├── src/
│   ├── lib/                     # 共通UIパーツ・ユーティリティ
│   │   ├── ui/                  #   Shadcn UIコンポーネント (Button, Card, Input)
│   │   ├── layout/              #   Header, PageLayout
│   │   ├── hooks/               #   useApi, useDebounce
│   │   └── types/               #   共通型定義
│   ├── features/                # ドメイン別機能
│   │   ├── search/              #   コース検索
│   │   ├── recommend/           #   推薦・学習パス
│   │   └── chat/                #   チャットUI
│   └── app/                     # エントリポイント・ルーティング
```

### 構造の選択: Feature-based を選んだ理由

| 選択肢 | 棄却理由 |
|--------|---------|
| **Atomic Design** | 2013年提唱。UIの粒度（atoms/molecules/organisms）で分類するが、「これはMoleculeかOrganismか」で迷いやすい。デザインチームとの協業で真価を発揮するが、1人開発では恩恵が薄い |
| **フロントエンドClean Architecture** | バックエンド向けのパターン。フロントは「UIとインタラクション」が中心で、ポート/アダプタで守るべき「ドメインロジック」が薄い。domain/usecasesに書くものが少なくなる |
| **フラットなcomponents/構成** | 小規模には十分だが、機能が増えた時にファイルが散らばる |

Feature-basedを選んだ理由:
- バックエンドのクリーンアーキテクチャと構造が対応する（search, recommend, chat）
- 「この機能を変更する」時にフロント・バック両方で見るべき場所が明確
- Bulletproof React（Reactベストプラクティス集）で推奨されている構成
- `lib/` にAtomic Design的な共通UIパーツを置くハイブリッド構成で、両方の利点を取り入れ

### Consequences
- ✓ AI（Claude, Cursor等）がTailwindクラスの生成に非常に強く、開発速度が上がる
- ✓ Shadcn UIのコピペ式で必要なコンポーネントだけ追加 → バンドルサイズ最小
- ✓ Feature-based構成がバックエンドと対応し、全体の見通しが良い
- ✗ Bun + Viteの組み合わせは比較的新しく、エッジケースでのトラブル可能性

---

## ADR-007: VectorDB選定 — Qdrant

### Status: Accepted

### Context
Courseraデータセット（6,645件、将来的に増加見込み）のベクトル埋め込みを保存し、セマンティック検索を実行する。仕様書Req2ではハイブリッド検索（ベクトル+キーワード）が求められている。商用デプロイを前提とするため、クライアント-サーバー型のDBが必須。

### Decision
**Qdrant** を採用する。

選定理由:
1. **ハイブリッド検索がネイティブ対応** — Req2の「Hybrid search combining vector similarity with keyword matching」をDB機能だけで実現。自前実装不要
2. **配列フィルタ `match_any`** — Courseraデータの `Skills` カラム（リスト形式）の検索に自然にフィット
3. **型付きPython API** — `PointStruct`, `Filter` 等の型付きモデルがClean Architectureのドメイン層と相性が良い
4. **商用対応** — Qdrant Cloud（マネージド）、セルフホスト（Docker/K8s）両方に対応。レプリケーション、スナップショットバックアップ、APIキー認証、Prometheus metrics対応
5. **Docker Composeに自然に収まる** — 1コンテナで起動、モジュラーモノリス構成にフィット
6. **Grafanaモニタリング** — Prometheusメトリクス公開によりGrafanaダッシュボードで監視可能

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **ChromaDB** | ハイブリッド検索が未対応（BM25等の全文検索がない）。組み込み型でプロセス分離がなく、商用デプロイに不適。同時アクセス・独立スケーリング不可 |
| **Weaviate** | ハイブリッド検索対応で有力だったが、Dockerイメージが重い（~1GB）、モジュール設定が複雑。GraphQL APIはアダプタ層が厚くなる |
| **Milvus Lite** | 組み込み型でファイルベース。商用デプロイに不適（プロセス分離なし、同時アクセス不可） |
| **Milvus (フル版)** | 6,645件に対して5-6コンテナはオーバーキル。運用負荷が高い |
| **Pinecone** | フルマネージドSaaSでベンダーロックイン。ローカル開発環境を構築できない |
| **LanceDB** | ファイルベース（組み込み型）。v0.x系で破壊的変更リスク。商用運用の実績が少ない |
| **Pgvector** | RDBと統合できるメリットがあるが、ベクトル特化機能（ハイブリッド検索、配列フィルタ）は自前実装が必要 |
| **FAISS** | ライブラリであってDBではない。メタデータフィルタリングなし、永続化も自前実装 |

### Deployment Strategy
- **開発**: Docker Composeでローカルに `qdrant/qdrant` コンテナを起動
- **商用**: Qdrant Cloud（マネージド）またはクラウドVM上のDockerコンテナ
- **切り替え**: Clean Architectureのアダプタ層で接続先URLを変更するのみ（`localhost:6333` → `cloud-endpoint:6333`）

### Consequences
- ✓ ハイブリッド検索を追加実装なしで仕様書要件を満たせる
- ✓ Rust製で軽量・高速。メモリフットプリントが小さい
- ✓ Prometheus metrics → Grafanaダッシュボードでの監視が自然に実現
- ✓ 開発→商用の移行がURL変更のみ
- ✗ ローカル開発にDockerが必須（pip installだけでは動かない）
- ✗ ChromaDBほどの手軽さはない（ただし商用前提では問題にならない）

---

## ADR-008: UI/UX設計 — マルチページ・チャット中心型

### Status: Accepted

### Context
仕様書では「シンプルなUI」と記載されているが、プロダクトとして成立させるにはチャット画面だけでは不十分。コースブラウジング、学習パス可視化など、ユーザーが能動的に探索できるUIが必要。ユーザーはゴミゴミした画面を好まないため、洗練されたミニマルデザインを重視。

### Decision
**マルチページ構成 + チャット中心型UI** を採用する。

#### 画面構成

| 画面 | パス | 役割 |
|------|------|------|
| **Home** | `/` | ランディング。価値提案 + クイックスタート + 人気コース |
| **Explore** | `/explore` | コースカタログ。検索バー + フィルタ + カードグリッド |
| **Chat** | `/chat` | AI対話。検索・スキル分析・推薦。インライン結果表示 |
| **My Path** | `/path` | 学習パス管理・可視化。タイムライン + 進捗 |
| **Course Detail** | `/course/:id` | コース詳細。概要・スキルタグ・関連コース |
| **Settings** | `/settings` | プロフィール・学習目標設定 |

#### 画面間の導線

```
Home ─── 検索入力 ──→ Chat（AI対話開始）
  │                      │
  │                      ├─ コースカードクリック → Course Detail
  │                      │
  │                      └─ 「学習パスを生成」 → My Path
  │
  └── 「Explore」 ──→ Explore（カタログ閲覧）
                         │
                         └─ コースカードクリック → Course Detail
```

#### デザイン原則
- **ミニマル**: 余白を活かし、情報密度を抑える。1画面に1つの目的
- **一貫性**: ナビゲーション・カードデザイン・タイポグラフィを全画面で統一
- **段階的開示**: 最初は最低限の情報、クリック/展開で詳細を表示
- **レスポンシブ**: モバイル対応（Tailwind CSSのbreakpoints活用）

### UXテスト戦略
**Playwright** を使ったユーザビリティテストを実施。主要な導線（Home→Chat→結果→Course Detail→My Path）が自然に遷移できるか自動テストで検証。

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **チャットオンリー（ChatGPT型）** | アプリではなくチャットボット。ブラウジング・比較が困難。プロダクト感がない |
| **従来型カタログオンリー（Coursera型）** | AI機能の価値が見えづらい。差別化にならない |
| **SPA単一ページ（タブ切替）** | 機能が増えると1ページに詰め込みすぎ。URLで直接アクセスできない |

### Consequences
- ✓ プロダクトとして成立する複数画面構成
- ✓ チャットが中心だが、Explore・My Pathで能動的な操作も可能
- ✓ Playwrightで導線の品質を自動テスト可能
- ✗ 画面数が増える分、実装工数は増加（ただし Shadcn UI で効率化）

---

## ADR-009: LLMOps・モニタリング — Langfuse + Prometheus + Grafana

### Status: Accepted

### Context
商用デプロイを前提に、LLMの入出力トレーシング、インフラ監視、RAG品質評価の3層オブザーバビリティが必要。予算を最小限に抑えるため、OSS/無料枠のセルフホスティングを基本とする。

### Decision
以下の4ツールで構成する。すべてDocker Composeでセルフホスト可能。

| ツール | 役割 | 形態 |
|--------|------|------|
| **Langfuse** | LLMトレーシング（プロンプト入出力、トークン消費、エージェント実行フロー、コスト集計） | Docker常駐 |
| **Prometheus** | メトリクス収集（Qdrant検索レイテンシ、APIレスポンスタイム、エラー率） | Docker常駐 |
| **Grafana** | ダッシュボード・可視化・アラート（Prometheus + Langfuse APIの統合表示） | Docker常駐 |
| **DeepEval** | RAG品質評価（Faithfulness, Relevancy, Context Recall） | バッチ実行（pip install） |

#### 3層オブザーバビリティ

```
                  何を見るか                    いつ見るか
┌─────────────┐
│ Grafana      │  メトリクス（数値）            → リアルタイム監視
│ + Prometheus │  レイテンシ、エラー率、リソース
└──────────────┘
┌─────────────┐
│ Langfuse     │  トレース（構造化ログ）        → 問題発生時の原因追跡
│              │  プロンプト、レスポンス、トークン
└──────────────┘
┌─────────────┐
│ DeepEval     │  品質スコア（評価指標）        → 定期バッチ評価
│              │  Faithfulness, Relevancy
└──────────────┘
```

#### Docker Composeへの追加

```yaml
services:
  # ... (既存: frontend, api, ai-processing, qdrant)

  # === Observability ===
  prometheus:
    image: prom/prometheus
  grafana:
    image: grafana/grafana
  langfuse:
    image: langfuse/langfuse
  langfuse-db:
    image: postgres:16
```

合計 **8コンテナ** (app系4 + observability系4)

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **LangSmith** | LangChain社のSaaS。LangChain前提の設計で、Agents SDK（ADR-005）との統合には不向き |
| **OpenTelemetry + Grafana Tempo** | クラウドネイティブ標準だが、LLM特化のトレースUI（プロンプト/レスポンス表示）がない。Langfuseはこれを提供 |
| **カスタムPrometheus exporter** | 完全制御だが実装工数が大きい。Langfuseで代替可能 |
| **Datadog / New Relic** | 商用APM。高機能だが有料。OSS構成で十分 |

### 月額コスト試算

| 構成要素 | コスト |
|---------|--------|
| Langfuse（セルフホスト） | $0 |
| Prometheus（セルフホスト） | $0 |
| Grafana（セルフホスト） | $0 |
| DeepEval（pip install） | $0 |
| **合計（ツール費）** | **$0** |

※ ホスティングインフラ費は別途（ADR-007 Deployment Strategy参照）

### Consequences
- ✓ 全ツールOSSでセルフホスト → ツール費$0
- ✓ Docker Composeで一括起動 → 開発環境でも本番同等の監視
- ✓ 3層（メトリクス・トレース・品質評価）で網羅的なオブザーバビリティ
- ✓ Qdrant（ADR-007）のPrometheus metrics → Grafanaの連携がネイティブ
- ✗ Langfuseセルフホストにはpostgresが必要（コンテナ+1）
- ✗ Grafanaダッシュボードの設定は手動（初期セットアップ工数）

---

## ADR-010: エージェントアーキテクチャ — Triageパターン + 統一AIバックエンド

### Status: Accepted

### Context
仕様書Req2でマルチエージェント構成が求められている。ADR-005でOpenAI Agents SDKを採用済み。エージェントの構成パターンと、ユーザー導線（Explore検索バー / Chat画面）からのAIアクセス方式を決定する必要がある。

ユーザー視点では「裏でAIが動いているかどうかは関係なく、欲しい回答が返ってくればいい」。検索窓でもチャットでも、同じ品質のAI結果を提供すべき。

### Decision
**Triageパターン（4エージェント）** + **統一AIバックエンド** を採用する。

#### エージェント構成

```
                ┌─────────────┐
   ユーザー入力 → │ Triage Agent │ ← 入力を分類・ルーティング
                └──────┬──────┘
                       │ handoff()
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌─────────────┐ ┌──────────┐ ┌──────────┐
   │ Search Agent │ │ Skill Gap│ │ Path     │
   │             │ │ Agent    │ │ Agent    │
   │ コース検索   │ │ スキル分析│ │ 学習パス  │
   │ + フィルタ   │ │ + 比較   │ │ + 生成   │
   └─────────────┘ └──────────┘ └──────────┘
```

| エージェント | 役割 | 入力例 |
|-------------|------|--------|
| **Triage Agent** | 入力を分類し、適切なエージェントにhandoff | 全てのユーザー入力 |
| **Search Agent** | コース検索・フィルタリング。Qdrantハイブリッド検索を実行 | 「Python 初心者 コース」「機械学習 上級」 |
| **Skill Gap Agent** | 現在のスキルと目標を比較し、ギャップを分析 | 「データサイエンティストになるには何が足りない？」 |
| **Path Agent** | スキルギャップに基づいて学習パスを生成・最適化 | 「3ヶ月でWeb開発を学ぶプランを作って」 |

#### 統一AIバックエンド — Explore と Chat の共通化

```
┌─────────────────────────────────────────────────────┐
│ Frontend                                             │
│                                                      │
│  Explore (/explore)          Chat (/chat)            │
│  ┌──────────────┐            ┌──────────────┐       │
│  │ 検索バー      │            │ チャット窓    │       │
│  │ + フィルタ    │            │ + 入力欄      │       │
│  └──────┬───────┘            └──────┬───────┘       │
│         │                          │                 │
│         │  キーワード/会話文         │  自然言語       │
│         └──────────┬───────────────┘                 │
│                    │                                  │
└────────────────────┼──────────────────────────────────┘
                     ▼
              ┌─────────────┐
              │ Triage Agent │  ← 同じエンドポイント
              └──────┬──────┘
                     │
           出力フォーマットが違うだけ
           │                    │
    Explore向け:             Chat向け:
    カードグリッド +          会話形式 +
    AI要約（Google風）       インラインカード
```

**ポイント**: Explore検索バーとChat画面は同じTriage Agentを呼ぶ。違いは**出力フォーマット**のみ。

#### Explore検索バーの挙動（Google風）

```
検索入力 → Triage Agent → Search Agent → 結果返却
                                          │
                                ┌─────────┴─────────┐
                                │                    │
                          AI要約パネル         通常の検索結果
                          (上部に表示)         (カードグリッド)
```

- **キーワード入力**（例: `Python 機械学習`）→ AI要約 + コースカードグリッドを表示
- **会話的入力**（例: `初心者がデータサイエンスを学ぶにはどうしたらいい？`）→ Chat画面にリダイレクト（検索バーでは会話を続けられないため）

### Triageパターンを選んだ理由

| パターン | 構造 | 棄却理由 |
|---------|------|---------|
| **Sequential（直列）** | Agent A → Agent B → Agent C | 全入力が全エージェントを通過。「コース検索」だけの時にスキル分析・パス生成は不要 |
| **Orchestrator（指揮者）** | 中央がサブタスク分解・結果統合 | 入力が複合的でない限りオーバーキル。「Pythonコースを探して」に分解は不要 |
| **Triage（振り分け）** | 入力を分類→1つのエージェントにhandoff | ✓ ユーザー導線（検索/分析/パス生成）と1:1対応。シンプルで効率的 |

### ユーザー導線とエージェントの対応

| ユーザー行動 | 画面 | 呼ばれるエージェント |
|-------------|------|-------------------|
| 検索バーにキーワード入力 | Explore | Triage → Search Agent |
| 検索バーに会話文入力 | Explore → Chat | リダイレクト後 Triage が判断 |
| 「〇〇のコースを探して」 | Chat | Triage → Search Agent |
| 「私のスキルを分析して」 | Chat | Triage → Skill Gap Agent |
| 「学習プランを作って」 | Chat | Triage → Path Agent |
| 「Pythonのスキルギャップをもとにプランを作って」 | Chat | Triage → Skill Gap → Path（連鎖） |

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **Explore = API直接 / Chat = Agent経由（分離型）** | ユーザー視点では同じ入力に対して結果品質が異なるのは不自然。統一バックエンドが望ましい |
| **チャットオンリー（検索バーなし）** | Explore画面が無意味になる。ブラウジング体験が失われる |
| **検索バー = 単純キーワード検索のみ** | AI要約がないため差別化にならない。Google検索のようなAI統合ができない |

### Consequences
- ✓ Triage → handoff のシンプルなフローで拡張・デバッグが容易
- ✓ ユーザー導線（検索/分析/パス生成）とエージェントが1:1対応
- ✓ Explore・Chat共通バックエンドでAI体験が統一
- ✓ Google風のAI要約 + 通常結果のハイブリッド表示で差別化
- ✓ Agents SDKの `handoff()` で自然に実装可能
- ✗ Triage Agentの分類精度がUX全体に影響（曖昧な入力の振り分けが課題）
- ✗ Explore向け・Chat向けで出力フォーマットを分けるロジックが必要

---

## ADR-011: インフラ・デプロイ戦略 — GCP Cloud Run + マネージド無料枠

### Status: Accepted

### Context
商用デプロイを前提に、月額コストを最小限に抑えつつ、プロダクションレディなインフラを構築する必要がある。ADR-001でDocker Compose + モジュラーモノリスを採用済み。開発環境では8コンテナ構成（ADR-009）だが、本番では全てをVM上で動かす必要はない。

### Decision
**本番: GCP Cloud Run + マネージド無料枠**、**開発: Docker Compose 全8コンテナ** の二段構成を採用する。

#### 本番構成

| サービス | ホスティング先 | 月額 |
|---------|--------------|------|
| Frontend (React SPA) | Firebase Hosting（CDN配信） | $0 |
| API (Hono) | Cloud Run | $0~$1 |
| AI Processing (Python) | Cloud Run | $0~$2 |
| Grafana (ダッシュボード) | Cloud Run（Provisioning as Code） | $0 |
| Qdrant (VectorDB) | Qdrant Cloud（無料枠 1GB） | $0 |
| メトリクス収集 | GCP Cloud Monitoring（組み込み） | $0 |
| LLM API | OpenAI (GPT-4o-mini) | ~$5 |
| Embedding API | OpenAI (text-embedding) | ~$1 |
| **合計** | | **~$6/mo** |

```
本番
┌────────────────────────────────────────────┐
│  Firebase Hosting:     Frontend (CDN)       │
│  Cloud Run:            API (Hono)           │
│  Cloud Run:            AI Processing (Py)   │
│  Cloud Run:            Grafana              │
│  Qdrant Cloud:         VectorDB (1GB free)  │
│  GCP Cloud Monitoring: メトリクス (組み込み)  │
└────────────────────────────────────────────┘
```

#### 開発構成

```
開発 (docker compose up)
┌────────────────────────────────────────────┐
│  App: frontend, api, ai-processing, qdrant │
│  Obs: prometheus, grafana, langfuse, pg    │
│  Eval: DeepEval (pip, バッチ実行)           │
└────────────────────────────────────────────┘
```

#### Observabilityの環境別構成

| ツール | 開発（ローカル） | 本番 |
|--------|----------------|------|
| **メトリクス収集** | Prometheus (Docker) | GCP Cloud Monitoring (組み込み) |
| **ダッシュボード** | Grafana (Docker) | Grafana (Cloud Run) |
| **LLMトレーシング** | Langfuse (Docker) | ローカルのみ（必要時 Langfuse Cloud 無料枠追加可） |
| **RAG品質評価** | DeepEval (pip) | ローカルのみ（バッチ実行） |

ダッシュボード定義（JSON/YAML）は開発・本番で共有。データソースのみ環境変数で切り替え。

#### Grafana on Cloud Run: Provisioning as Code

```
grafana/
├── provisioning/
│   ├── datasources/
│   │   └── gcp.yml            # 本番: GCP Cloud Monitoring
│   │   └── prometheus.yml     # 開発: ローカルPrometheus
│   └── dashboards/
│       ├── dashboard.yml
│       └── cloud-run.json     # 共通ダッシュボード定義
└── Dockerfile
```

ダッシュボード設定をDockerイメージにbake → コンテナが再起動しても自動再構築（ステートレス化）。

#### Cloud Run 無料枠（月あたり、恒久）

| リソース | 無料枠 |
|---------|--------|
| リクエスト | 200万回 |
| vCPU | 180,000秒（≒50時間） |
| メモリ | 360,000 GB秒 |
| Egress | 1GB |

キャプストーンのデモ用途では十分な枠。

#### コールドスタートの注意

Cloud Runはリクエストがない時コンテナを停止する。再起動時にコールドスタート遅延が発生:
- API (Hono/Bun): ~1-2秒
- AI Processing (Python + ML libs): ~5-15秒

デモ時の対策: `min-instances=1` で最低1コンテナを常時起動、または事前にウォームアップリクエストを送信。

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **単一VM + Docker Compose（GCP e2-medium）** | 月額~$32。マネージドサービスを使わないならクラウドの恩恵がVM料金に見合わない |
| **VPS（さくら、Xserver等）+ Docker Compose** | 月額~$15で安いが、GCPエコシステム（Cloud Monitoring、Firebase）の恩恵がない。将来のGCPマネージド移行に追加工数 |
| **GKE / GKE Autopilot** | 最低 ~$74/mo。8コンテナにKubernetesはオーバーキル |
| **Grafana Cloud（マネージド）** | 無料枠で動くが、自前構築の方がキャプストーンの設計力アピールになる |
| **全サービスCloud Run（Observability含む）** | Langfuse + PostgreSQLはステートフル。Cloud Runとの相性が悪い |

### 月額コスト比較（最終版）

| 構成 | インフラ費 | LLM API | 合計 |
|------|----------|---------|------|
| **Cloud Run + 無料枠（採用）** | ~$0 | ~$6 | **~$6/mo** |
| VPS (Xserver 4GB) | ~$15 | ~$6 | ~$21/mo |
| GCP VM (e2-medium) | ~$32 | ~$6 | ~$38/mo |
| GKE Autopilot | ~$74 | ~$6 | ~$80/mo |

### Consequences
- ✓ インフラ費実質$0。LLM API費のみで商用デプロイ可能
- ✓ Cloud Runの無料枠は恒久（毎月リセット）
- ✓ Firebase Hosting + Cloud Run + Qdrant Cloud の組み合わせで運用負荷が最小
- ✓ Grafana Provisioning as Codeでダッシュボードをバージョン管理
- ✓ 将来のGCPマネージド移行（Vertex AI等）がエコシステム内で完結
- ✗ コールドスタート遅延（AI処理で5-15秒）。デモ時は対策が必要
- ✗ 開発（Docker Compose）と本番（Cloud Run）でデプロイ方式が異なる
- ✗ 本番でLangfuseが使えない（必要時はLangfuse Cloud無料枠で対応可）

---

## 技術スタック全体像

```
=== 本番 (GCP) ===

┌─────────────────────────────────────────────────────────┐
│                      Frontend                            │
│           Bun + React (Vite) + Shadcn UI                │
│           Firebase Hosting (CDN配信)                     │
│           Pages: Home, Explore, Chat, My Path, Detail   │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP (REST + SSE)
┌─────────────────────▼───────────────────────────────────┐
│                    API Layer — Cloud Run                  │
│              Bun + Hono (TypeScript)                     │
│       ルーティング、認証、リクエストバリデーション           │
│     ※ FastAPI統一案も候補として保留                       │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP (REST)
┌─────────────────────▼───────────────────────────────────┐
│              AI Processing Layer — Cloud Run              │
│            Python + Litestar (or FastAPI)                │
│            クリーンアーキテクチャ                          │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌───────────────┐            │
│  │ Agents   │ │ RAG      │ │ Evaluation    │            │
│  │ (SDK)    │ │ (自前)   │ │ (DeepEval)    │            │
│  └──────────┘ └──────────┘ └───────────────┘            │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
┌──────────▼──────────┐  ┌───────────▼────────────────────┐
│     Data Layer      │  │     Observability Layer         │
│  Qdrant Cloud       │  │  GCP Cloud Monitoring (組み込み) │
│  (無料枠 1GB)       │  │  Grafana on Cloud Run           │
└─────────────────────┘  │  (Provisioning as Code)         │
                         └────────────────────────────────┘

=== 開発 (ローカル Docker Compose) ===

  App:  frontend + api + ai-processing + qdrant
  Obs:  prometheus + grafana + langfuse + langfuse-db
  Eval: DeepEval (pip, バッチ)
```

---

## 未決定事項

| 項目 | 候補 | 決定期限 |
|------|------|---------|
| ~~VectorDB~~ | ~~Qdrant~~ | ~~Accepted (ADR-007)~~ |
| ~~UI/UX設計~~ | ~~マルチページ・チャット中心型~~ | ~~Accepted (ADR-008)~~ |
| ~~LLMOps・モニタリング~~ | ~~Langfuse + Prometheus + Grafana~~ | ~~Accepted (ADR-009)~~ |
| API層の最終決定 | Bun+Hono / FastAPI統一 | ヒアリング後 |
| AI処理層フレームワーク | Litestar / FastAPI | ヒアリング後 |
| UIアニメーション | Magic UI / Aceternity UI / 両方 | 実装フェーズ |
| 通信プロトコル | REST / SSE（ストリーミング用） | 設計フェーズ |
| ~~RAGパイプライン詳細~~ | ~~ADR-012で決定~~ | ~~Accepted (ADR-012)~~ |
| ~~エージェント構成~~ | ~~Triageパターン、4エージェント~~ | ~~Accepted (ADR-010)~~ |
| ~~インフラ・デプロイ~~ | ~~Cloud Run + Firebase Hosting + Qdrant Cloud~~ | ~~Accepted (ADR-011)~~ |
| ~~テスト戦略~~ | ~~DeepEval + Golden Dataset + CI/CD~~ | ~~Accepted (ADR-012-7)~~ |
| ~~CI/CDパイプライン~~ | ~~GitHub Actions (Public)~~ | ~~Accepted (ADR-012-8)~~ |
| ~~環境設定・シークレット管理~~ | ~~Docker Compose + Pydantic Settings~~ | ~~Accepted (ADR-012-9)~~ |
| ~~Gitブランチ戦略~~ | ~~GitHub Flow + Issue駆動~~ | ~~Accepted (ADR-012-10)~~ |
| ~~MCP Server~~ | ~~OAuth 2.1 + Keycloak（ストレッチ）~~ | ~~Accepted (ADR-012-11)~~ |

---

## ADR-012: RAGパイプライン設計

### Status: Accepted

### Context
Courseraデータセット（6,645件、CSV）をベクトル検索可能にし、4エージェント（ADR-010）が高精度な検索を行えるRAGパイプラインを設計する必要がある。データは構造化カタログであり、従来の長文ドキュメント向けチャンキングは不要。ただしSkillsフィールドが29%空であり、Descriptionの品質にバラつきがある。

### Decision

#### 12-1: Embedding対象 — LLM前処理 + テンプレート連結

**方式**: Ingestion時にGPT-4o-miniで各コースの検索用テキストを生成し、それをembedする。

**前処理の目的**:
- Skills空（29%）の補完: Descriptionからスキルを推定
- Description品質の正規化: 冗長表現を除去し、検索キーワードを凝縮
- 全件で一貫した形式のテキストを生成

**Ingestion Pipeline**:
```
CSV読込 → LLM前処理（Skills補完・検索用テキスト生成）→ Embedding → Qdrant
                ↓
           生データはmetadataとして保存（LLMコンテキスト用）
```

**コレクション設計**: 単一コレクション + メタデータフィルタ（6,645件の規模では分割不要）

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| 生データ直接連結（LLM前処理なし） | Skills空29%が検索精度のボトルネック。Description品質のバラつきもベクトル品質に影響 |
| Named Vectors（複数ベクトル/ドキュメント） | 6,645件の規模では複雑さに見合わない。Qdrant固有機能でポータビリティが下がる |
| 分割コレクション（courses + skills） | データ量が少なく分割メリットなし。メタデータフィルタで代替可能 |

**前処理コスト**: ~$1.10（1回きり）

---

#### 12-2: Embeddingモデル — text-embedding-3-large

**モデル**: OpenAI `text-embedding-3-large`（3072次元）

**選定理由**:
- 6,645件のembedding生成コストは$0.26（1回きり）。smallとの差額$0.22は誤差
- MTEB精度 64.6%（smallの62.3%より高い）
- コスト差が無視できる規模では、精度が高い方を選ばない理由がない
- 再embeddingが必要になっても数分+数十セントで完了する規模

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| text-embedding-3-small | コスト差$0.22で精度を妥協する理由がない |
| text-embedding-ada-002 | 旧世代。精度・コスト両面で3系に劣る |
| OSS (e5-large等) | トークン上限512が短い。LLM整形後テキストが収まらない可能性。インフラ管理コスト |

**ストレージ**: 6,645件 × 3072次元 × 4bytes ≒ 80MB。Qdrant Cloud無料枠1GBに十分収まる

---

#### 12-3: ハイブリッド検索戦略 — Dense + Sparse + RRF

**構成**: メタデータフィルタ → Dense + Sparse 並列検索 → RRF統合

```
ユーザークエリ
    │
    ▼
Step 1: メタデータフィルタ（Level, Organization等で絞り込み）
    │
    ▼
Step 2: Dense + Sparse 並列検索
    │  Dense:  text-embedding-3-large によるベクトル類似度（意味検索）
    │  Sparse: Qdrant Sparse Vector によるキーワードマッチ（BM25相当）
    │
    ▼
Step 3: RRF（Reciprocal Rank Fusion）でスコア統合
    │
    ▼
top_k = 20件 → リランキングへ（12-5）
```

**Dense と Sparse の役割分担**:

- **Dense**: 意味的に近いがキーワードが異なるコースを発見（例: 「AIを学びたい」→「Machine Learning Specialization」）
- **Sparse**: 固有名詞・技術用語の正確な一致（例: 「TensorFlow」→ タイトルにTensorFlowを含むコース）

**スコア統合にRRFを選んだ理由**:

- 重み付き線形結合（`α × Dense + (1-α) × Sparse`）はDenseとSparseでスコアの尺度が異なるため正規化が必要
- RRFは**順位ベース**で統合するため正規化不要。Qdrantがネイティブ対応しており実装コストゼロ

**クエリ最適化**: パイプラインには含めない。Search Agentのinstructionsで対応。Agents SDKのエージェントはLLM自体なので、クエリの言い換えや再検索（Corrective RAG パターン）を自律的に実行可能。

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| Dense only | 仕様書Req2が「Hybrid search combining vector embeddings and keyword retrieval」を要求。固有名詞検索でSparseに劣る |
| Multi-Query（複数クエリ並列） | レイテンシが3倍。6,645件のカタログ検索ではHybridで十分な精度 |
| Graph RAG | Courseraデータにprerequisite情報が明示的に含まれない。LLM推定の精度保証が困難。Could Haveとして保留 |
| 重み付き線形結合 | スコア正規化の実装が必要。RRFの方がシンプルで同等以上の性能 |

**今後の検討事項**:

- キャッシュ戦略: 頻出クエリの検索結果キャッシュ（レイテンシ削減 + LLM API費削減）
- Graph RAG: prerequisite関係をLLMで推定しグラフ化（Could Have）

---

#### 12-4: メタデータフィルタリング — Qdrant payload + エージェント駆動フィルタ

**設計方針**: フィルタ可能な属性はQdrantのpayloadフィルタで処理し、意味的な検索はDense+Sparseに任せる。フィルタの組み立てはSearch Agentがツールパラメータ経由で行う。

**payloadスキーマ**:

| フィールド | 型 | フィルタ種別 | 用途 |
|-----------|-----|------------|------|
| `level` | string | 完全一致 | 難易度絞り込み（Beginner/Intermediate/Advanced） |
| `organization` | string | 完全一致 / match_any | 提供組織 |
| `rating` | float | 範囲（≥ N） | 高評価フィルタ |
| `skills` | list[string] | match_any | スキルで絞り込み |
| `enrolled` | int | 範囲 | 人気度 |
| `num_reviews` | int | 範囲 | 信頼性フィルタ |
| `title` | string | 表示用 | LLMコンテキスト |
| `description` | string | 表示用 | LLMコンテキスト |
| `url` | string | 表示用 | フロントエンドリンク |
| `modules` | string | 表示用 | コース構成情報 |
| `schedule` | string | 表示用 | 所要時間 |
| `instructor` | string | 表示用 | 講師名 |

**フィルタとセマンティック検索の境界**:

- **フィルタで処理**: Level, Organization, rating, enrolled（確実に一致/範囲で絞り込む属性）
- **Dense検索で処理**: コース内容、キャリア適合度（意味的な関連性）
- **両方で処理**: Skills（match_anyフィルタ + embeddingにも含む）

**欠損データの扱い**:

- Level欠損（778件/12%）: フィルタ指定時、欠損（None）も結果に含める。優良コースの見逃し防止
- Skills空（1,954件/29%）: Decision 12-1のLLM前処理で補完済み。フィルタ時はSkills空のコースもデフォルトで除外しない
- rating: 全件あり。デフォルト閾値は設けない（エージェント判断）

**Search Agentのツール設計**:

```python
@function_tool
def search_courses(
    query: str,
    level: str | None = None,
    organization: str | None = None,
    min_rating: float | None = None,
    skills: list[str] | None = None,
    limit: int = 10
) -> str:
```

エージェントがユーザーの自然言語（「初心者向け」「評価高いやつ」）をツールパラメータに変換する。フィルタ組み立てロジックの自前実装が不要。

---

#### 12-5: リランキング戦略 — Strategy パターンで3手法を比較評価

**設計方針**: リランキングの有無・手法によるRAG精度への影響を定量的に検証する。Golden Datasetを使い、3つのStrategyを切り替えてA/B比較し、コストに見合う精度向上があるかを判断する。

**パイプライン上の位置**:

```
Hybrid Search (12-3) → top_k=20件
    │
    ▼
Reranking（Strategy パターンで切り替え）
    │
    ▼
Result Selection: Top-k + Threshold
    │  → 上位k件を選択、かつ閾値以下を除外
    │  → 件数不足時は Corrective RAG（クエリ再構成→再検索）
    │
    ▼
Context Assembly (12-6) へ
```

**3つのStrategy**:

| Strategy | 手法 | コスト | レイテンシ |
|----------|------|--------|-----------|
| `none` | パススルー（ベースライン） | $0 | 0ms |
| `heuristic` | 重み付きスコア: `α × relevance + β × rating + γ × enrolled` | $0 | ~1ms |
| `cross-encoder` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | $0 | +200-500ms (CPU) |

**切り替え方式**: 環境変数 `RERANKER_STRATEGY` で制御。Pythonの Strategy パターンで実装。

```python
class BaseReranker:
    def rerank(self, query: str, results: list[dict], top_k: int) -> list[dict]:
        raise NotImplementedError

class NoReranker(BaseReranker):       # パススルー
class HeuristicReranker(BaseReranker): # 重み付きスコア
class CrossEncoderReranker(BaseReranker): # Neural Re-ranking
```

**Result Selection**:

- Top-k: リランキング後の上位k件を返す（デフォルトk=10、エージェントがlimitパラメータで制御）
- Threshold: 類似度スコアが閾値未満の結果を除外（閾値はGolden Datasetで調整）
- 件数不足時: Search Agentが Corrective RAG パターンでクエリを再構成し再検索

**評価計画**: Golden Dataset（Decision 12-7で定義）を使い、以下を測定:

- Retrieval Accuracy（正しいコースが上位に来るか）
- Precision@k / Recall@k
- レイテンシ
- 3 Strategy間の精度差がコスト（レイテンシ含む）に見合うかで最終選定

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| Cohere Rerank API | 精度は最高だが有料（$1/1000検索）。まず無料手法で十分な精度が出るか検証してからの判断 |
| LLM-as-Reranker | レイテンシ+1-3秒、コスト高。リアルタイム検索には不向き |
| Learning to Rank (LTR) | 訓練データが必要。6,645件の規模ではデータ不足 |
| Cohere追加（将来） | 無料手法で精度不足が判明した場合に4つ目のStrategyとして追加可能 |

---

#### 12-6: コンテキスト組み立て — TOON/JSON 切り替え + Hallucination防止

**設計方針**: 検索結果をLLMに渡すフォーマットを差し替え可能にし、トークン効率と精度を比較評価する。フォーマッターはマイクロモジュールとして実装し、不要時は即座に削除可能にする。

**パイプライン上の位置**:

```
Reranking (12-5) → Result Selection
    │
    ▼
Formatter（マイクロモジュール）
    ├── JsonFormatter   → json.dumps（ベースライン）
    └── ToonFormatter   → TOON変換（トークン約50%削減）
    │
    ▼
Search Agent のツール戻り値として返却
    │
    ▼
Agents SDK が自動的に LLM コンテキストに挿入 → 回答生成
```

**フォーマット比較**:

| 形式 | トークン消費 | メリット | リスク |
|------|------------|---------|--------|
| JSON | 多い（キー名×件数の繰り返し） | LLM理解度が確実、デバッグ容易 | コンテキスト枠を圧迫 |
| TOON | **約50%削減** | 同じ予算でより多くの結果を含められる | 比較的新しいフォーマット、LLM理解度の検証が必要 |

**TOON (Token-Oriented Object Notation) 形式**:

```
courses[3]{title,org,level,rating,enrolled,skills}:
  ML Specialization,Stanford,Beginner,4.8,12345,"Python, TensorFlow"
  Deep Learning,DeepLearning.AI,Intermediate,4.9,8901,"Neural Networks, CNN"
  NLP Specialization,DeepLearning.AI,Advanced,4.7,5432,"NLP, Transformers"
```

JSONではフィールド名が件数分繰り返されるが、TOONではヘッダー1行のみ。10件返す場合、6フィールド×10件=60回のキー名繰り返しが解消される。

**ToonFormatter の設計原則**:

- **1ファイル、外部依存なし、Pure Python** で実装
- 不要になったらファイル削除 + Formatter差し替えのみで完全除去可能
- 環境変数 `CONTEXT_FORMAT=json|toon` で切り替え

**Hallucination防止策**:

Search Agent の instructions に以下を明記:
- 「検索結果に含まれるコースのみ紹介すること」
- 「結果にないコースを推薦・創作しないこと」
- 「価格・評価・スキル等のデータは検索結果の値を正確に引用すること」

これはproduct-discoveryプロジェクトの RetrievalAgent と同じパターン。

**トークン予算管理**:

- `max_context_length` パラメータでツール戻り値の上限を制御
- TOON形式なら同じ予算でJSON比約2倍のコース情報を含められる
- 予算超過時は低スコアの結果から切り捨て

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| JSON固定 | トークン効率が悪い。TOON比較の余地を残すべき |
| TOON固定 | LLM理解度が未検証。JSON をベースラインとして残す |
| Markdown テーブル形式 | TOONよりトークン効率が悪い（罫線文字のオーバーヘッド） |
| XML形式 | 冗長。JSON以上にトークンを消費する |

---

#### 12-7: テスト戦略 — 3層テスト + Golden Dataset + DeepEval

**設計方針**: テストを3層に分け、各層の役割を明確にする。RAG評価はGolden DatasetとDeepEvalで定量化し、CI/CDゲートとして機能させる。

**テスト3層構成**:

```
Layer 1: Unit Tests（pytest）
    → Formatter（JSON/TOON）、Reranker各Strategy、メタデータフィルタ構築
    → 入出力が確定的なコンポーネントの正確性を検証
    → 実行: 毎コミット

Layer 2: RAG Evaluation（DeepEval + Golden Dataset）
    → 検索パイプライン全体の品質を測定
    → Strategy比較（Reranker 3種、Formatter 2種）
    → 実行: PR作成時 / 手動トリガー

Layer 3: E2E Agent Tests（LLM-as-Judge）
    → ユーザークエリ → エージェント応答の品質評価
    → 4エージェント（Triage, Search, SkillGap, Path）の統合テスト
    → 実行: リリース前 / 手動トリガー
```

**Golden Dataset（80-100件）**:

| カテゴリ | 件数 | 内容 |
|---------|------|------|
| Search系（手動） | 10件 | キーワード検索、自然言語検索の期待コース |
| SkillGap系（手動） | 5件 | スキルギャップ分析の期待スキル+コース |
| Path系（手動） | 5件 | 学習ロードマップの期待コース順序 |
| フィルタ組み合わせ（手動） | 5件 | Level×Organization等のメタデータフィルタ検証 |
| エッジケース（手動） | 5件 | 存在しないトピック、曖昧クエリ、空結果 |
| LLM逆生成 | 50-70件 | 実在コースから「このコースを見つけるクエリ」を生成 |

件数の根拠: 二値メトリクス（Hit Rate等）で95%信頼度・±10%信頼区間を得るには約100サンプルが必要。80-100件は統計的信頼性と作成コストのバランス点。

**評価メトリクス（優先度順）**:

```
Tier 1（必須 — CI/CDゲート、閾値を下回ったらデプロイ停止）:
  ├── Hit Rate@10     — 正解コースがtop-10に含まれるか
  ├── Hallucination   — 存在しないコースの創作を検知
  └── Faithfulness    — コンテキスト情報のみの正確な引用

Tier 2（重要 — Strategy比較の判断基準）:
  ├── MRR             — 正解コースの順位（リランキング評価）
  └── NDCG@10         — ランキング品質（リランキング評価）

Tier 3（参考 — 改善指針）:
  ├── Precision@10    — 検索結果のノイズ量
  └── Answer Relevancy — エージェント応答の的確さ
```

**Strategy比較の実行計画**:

Decision 12-5（リランキング）とDecision 12-6（フォーマット）の比較をTier 2メトリクスで実施:

- Reranker: none vs heuristic vs cross-encoder → MRR, NDCG@10 で比較
- Formatter: JSON vs TOON → Faithfulness, Answer Relevancy + トークン消費量で比較

**回帰検知**:

- ベースラインスコアを記録し、プロンプト変更やモデル更新時に自動比較
- Tier 1メトリクスが閾値を下回った場合、CI/CDパイプラインでデプロイをブロック

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| テストなし（手動確認のみ） | 回帰を検知できない。プロンプト変更のたびに手動確認は非現実的 |
| 全件テスト（6,645コース対象） | Golden Dataset はクエリパターンの網羅が目的。データカバレッジは不要 |
| Layer 2のみ（Unit Test省略） | Formatter, Reranker等の確定的ロジックはUnit Testの方が高速・安定 |

---

#### 12-8: CI/CDパイプライン — GitHub Actions + paths フィルタ + GCPデプロイ

**設計方針**: GitHub Actions（Public リポジトリ）で3段階のパイプラインを構築。LLM Eval は paths フィルタでLLM関連ファイル変更時のみ実行し、APIコストを最小化する。

**リポジトリ方針**: **Public** リポジトリとして運用。

- GitHub Actions の分数制限なし（Private は月2,000分制限）
- キャップストーンのポートフォリオとしても活用
- APIキー・デプロイURL等は全て GitHub Secrets に格納

**パイプライン構成**:

```
Push / PR
    │
    ▼
┌─────────────────────────────────────────┐
│ Stage 1: Lint + Unit Test（全Push）     │
│  → ruff（Linter）                       │
│  → pytest（Layer 1: Unit Tests）        │
│  → 高速・無料・毎コミット               │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ Stage 2: LLM Eval（LLM関連変更時のみ） │
│  → paths フィルタで制御                 │
│  → DeepEval + Golden Dataset            │
│  → Tier 1 閾値未満 → マージブロック     │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ Stage 3: Deploy（main マージ後）        │
│  → Docker イメージ build + push         │
│  → GCP Cloud Run へデプロイ             │
└─────────────────────────────────────────┘
```

**paths フィルタ（Stage 2 のトリガー条件）**:

```yaml
# LLM Eval は以下のパスが変更された PR でのみ実行
on:
  pull_request:
    paths:
      - 'src/agents/**'        # エージェント instructions
      - 'src/rag/**'           # RAGパイプライン
      - 'src/search/**'        # 検索ロジック
      - 'src/reranking/**'     # リランカー
      - 'src/formatters/**'    # JSON/TOON フォーマッター
      - 'config/prompts/**'    # プロンプトテンプレート
      - 'config/models.*'      # モデル設定
```

フロントエンド修正やドキュメント変更では Stage 2 が走らず、APIコストを節約。

**セキュリティ（Publicリポジトリ対策）**:

| 保護対象 | 対策 |
|---------|------|
| APIキー（OpenAI, Qdrant等） | GitHub Secrets に格納。コードに直書きしない |
| デプロイ先URL・GCPプロジェクトID | GitHub Secrets に格納 |
| デプロイ済みサービス | Cloud Run `--no-allow-unauthenticated`（Google認証必須） |
| デモ時のアクセス提供 | Bearer Token 方式に一時切り替え、トークンを審査員に提供 |

**デプロイ先**: GCP Cloud Run（詳細設計は別ADRで決定）

- Docker Compose で開発 → Cloud Run でデプロイの流れが自然
- Qdrant Cloud（外部）+ OpenAI API（外部）は Cloud Run から接続

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| Private リポジトリ | GitHub Actions 月2,000分制限。LLM Eval は時間がかかるため制限に抵触するリスク |
| 全PR で LLM Eval 実行 | フロントエンド修正でも API コストが発生。paths フィルタで解決 |
| AWS / Azure | GCPでの開発予定があり、学習コスト統一のため GCP を選択 |
| 手動デプロイ | ヒューマンエラーのリスク。CI/CD で自動化すべき |

---

#### 12-9: 環境設定・シークレット管理 — Dev/Prod 自動分離 + Pydantic バリデーション

**設計方針**: 開発者がファイルを切り替える操作をゼロにする。Dev は `docker compose up` だけで動き、Prod は CI/CD が全自動で設定を注入する。

**設定の2分類**:

| 分類 | 管理方法 | 変更タイミング |
|------|---------|---------------|
| Infrastructure Config（API キー、DB 接続先等） | 環境変数 | 起動時に固定 |
| App Config（リランカー、フォーマット等） | DB or API | 実行時に UI から変更可能 |

**ファイル構成**:

```
docker-compose.yml          ← Dev 用（docker compose up でそのまま動く）
docker-compose.prod.yml     ← Prod バックアップ（VM デプロイ用、当面未使用）
Dockerfile                  ← イメージビルド（Dev / Prod 共通）
.env.local                  ← Dev の API キーのみ（.gitignore）
.env.example                ← 設定項目一覧（Git 管理、値は空）
```

**Dev 環境（ローカル）**:

```bash
# 初回セットアップ
git clone → echo "OPENAI_API_KEY=sk-xxx" > .env.local → docker compose up

# 2回目以降
docker compose up   # 何も変えない
```

```yaml
# docker-compose.yml（Dev 用）
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env.local
    environment:
      - APP_ENV=dev
      - QDRANT_URL=http://qdrant:6333

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

- Dev は Qdrant ローカルコンテナ（外部サービス依存なし、OpenAI API 以外）
- `.env.local` には `OPENAI_API_KEY` のみ記入

**Prod 環境（Cloud Run）**:

```bash
# CI/CD が実行（開発者は何もしない）
gcloud run deploy app \
  --set-env-vars "APP_ENV=prod" \
  --set-env-vars "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" \
  --set-env-vars "QDRANT_URL=${{ secrets.QDRANT_URL }}" \
  --set-env-vars "QDRANT_API_KEY=${{ secrets.QDRANT_API_KEY }}"
```

- .env ファイルは存在しない。GitHub Secrets → Cloud Run 環境変数に直接注入
- docker-compose は使わない（Cloud Run は Docker イメージ単体を実行）

**起動時バリデーション（Pydantic Settings）**:

```python
class Settings(BaseSettings):
    APP_ENV: Literal["dev", "prod"] = "dev"
    OPENAI_API_KEY: str                        # 必須 — 未設定→起動エラー
    QDRANT_URL: str = "http://qdrant:6333"     # Dev デフォルト
    QDRANT_API_KEY: str | None = None          # Dev は不要

    @model_validator(mode="after")
    def validate_prod(self):
        if self.APP_ENV == "prod" and not self.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY is required in production")
        return self
```

- Dev: デフォルト値で全て動く（OPENAI_API_KEY のみ必須）
- Prod: `APP_ENV=prod` 時に追加の必須チェックが走る
- 設定ミス → 起動時に即エラー（デプロイ後に気づくのではなく、起動時に検知）

**App Config（実行時変更可能な設定）**:

| 設定 | 選択肢 | デフォルト |
|------|--------|-----------|
| リランカー | none / heuristic / cross-encoder | none |
| コンテキスト形式 | JSON / TOON | json |
| 検索件数（top_k） | 5 / 10 / 20 | 10 |
| 類似度閾値 | 0.5 - 0.9 | 0.7 |

UI の設定画面から `PUT /api/settings` で変更 → パイプラインが次のリクエストから新設定を使用。デモ時に「リランカーを切り替えると精度がこう変わる」と見せられる。

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| .env.dev / .env.prod 手動切り替え | 切り替え忘れで Prod が Dev 設定で動くリスク |
| docker-compose.override.yml | 自動マージされるため、Prod 環境で意図せず Dev 設定が適用されるリスク |
| 環境変数のみ（バリデーションなし） | typo や未設定に実行時まで気づけない。Pydantic で起動時検知 |

---

#### 12-10: Git ブランチ戦略 — GitHub Flow + Issue 駆動 + カンバン管理

**設計方針**: GitHub Issues + GitHub Projects（カンバン）でタスク管理し、Issue 番号に紐づいたブランチ名で開発する。AI を駆使した分散開発（複数ブランチ並行）を前提とした構成。

**ブランチ構成**:

```
main ─────────────────── 本番環境（Cloud Run に自動デプロイ）
  │
  └── develop ────────── ローカル統合環境（feature 統合先）
        │
        ├── LM0001-feature/rag-hybrid_search
        ├── LM0002-feature/frontend-settings_page
        └── LM0003-fix/agents-triage_routing
```

- `main`: 保護ブランチ（直接 push 禁止）。マージ → Cloud Run 自動デプロイ
- `develop`: 統合ブランチ。feature ブランチの統合先
- `LM****-{type}/{scope}-{detail}`: 開発タスクブランチ

**ブランチ命名規則**:

```
{prefix}{kanbanID}-{type}/{scope}-{detail}
```

| 要素 | 説明 | 例 |
|------|------|-----|
| prefix | アプリ名略称（2文字） | `LM`（Lumineer） |
| kanbanID | Issue番号（4桁固定） | `0001`, `0210` |
| type | タスク種別 | `feature`, `fix` 等 |
| scope | 対象領域 | `rag`, `frontend` 等 |
| detail | 内容の要約（snake_case） | `hybrid_search` |

**task種別**:

| 種別 | 用途 |
|------|------|
| `feature` | 新機能追加 |
| `fix` | バグ修正 |
| `hotfix` | 本番緊急修正（main から直接切る） |
| `refactor` | 機能変更なしのコード改善 |
| `docs` | ドキュメント |
| `test` | テスト追加・修正 |
| `chore` | 依存更新、設定変更、CI修正等 |

**taskスコープ**:

| スコープ | 対象 |
|---------|------|
| `frontend` | React UI |
| `backend` | FastAPI、API エンドポイント |
| `rag` | 検索パイプライン（embedding, reranking, formatter） |
| `agents` | Agents SDK（Triage, Search, SkillGap, Path） |
| `data` | Ingestion、前処理、Golden Dataset |
| `infra` | Docker, CI/CD, GCP, 環境設定 |
| `mcp` | MCP Server |

複数スコープにまたがる場合は `+` で連結: `frontend+backend-payment_flow`

**ブランチ名の例**:

```
LM0001-feature/rag-hybrid_search
LM0002-feature/rag-reranker_strategy
LM0003-feature/frontend-settings_page
LM0004-feature/agents-triage_routing
LM0005-feature/data-ingestion_pipeline
LM0006-chore/infra-docker_compose
LM0007-feature/mcp-remote_server
LM0008-test/rag-golden_dataset
LM0009-fix/agents-hallucination_guard
LM0010-feature/frontend+backend-search_results
```

**フロー**:

```
通常:   develop → feature branch → PR → CI → develop → main
hotfix: main → hotfix branch → PR → main（+ develop にもマージ）
```

**GitHub Projects（カンバン）**:

```
Backlog → To Do → In Progress → Review → Done
```

- Issue作成時にカンバンに自動追加
- PR本文に `Closes #N` 記載 → マージ時に Issue 自動クローズ + カンバン自動移動
- Issue テンプレートに ADR 参照欄を含め、実装判断の根拠を追える構成

**Alternatives Considered**:

| 選択肢 | 棄却理由 |
|--------|---------|
| Git Flow（develop, release, hotfix） | 1人開発には過剰。release ブランチの管理コストが見合わない |
| Trunk-based（main のみ） | PRベースの LLM Eval が使えない。develop での統合検証ができない |
| Issue番号なしのブランチ名 | タスクとの紐付けが切れ、分散開発時にブランチの目的が追えなくなる |

---

#### 12-11: MCP Server — OAuth 2.1 認証 + RAG パイプライン共有（ストレッチ目標）

**位置づけ**: ストレッチ目標。本体（Web UI + RAG パイプライン）と疎結合であり、実装しなくても本体に影響なし。

**目的**: ユーザーが自分の AI ツール（Claude Desktop, Cursor, VS Code 等）から MCP 経由でコース検索・スキル分析・学習パス生成を利用可能にする。LLM 推論はサーバー側で完結するため、ユーザー側に OpenAI API キーが不要。

**アーキテクチャ**:

```
Web UI (Explore/Chat) ──→ ┐
                           ├→ Triage Agent → 同じ RAG パイプライン → 回答
MCP Client            ──→ ┘
```

入口が違うだけで、パイプラインは完全共有。MCP Server は `interfaces/mcp/` に配置し、既存の usecase / agent を呼ぶだけ。

**公開する MCP Tools**:

| Tool | 用途 | サーバー側処理 |
|------|------|--------------|
| `ask_course_finder` | 自然言語で何でも聞ける（メイン） | Triage Agent が全て処理 |
| `search_courses` | フィルタ付きコース検索 | 検索パイプラインのみ（LLM 推論なし） |
| `get_skill_gap` | スキルギャップ分析 | SkillGap Agent が処理 |
| `get_learning_path` | 学習パス生成 | Path Agent が処理 |

**認証認可: OAuth 2.1（MCP 公式標準）**:

MCP 仕様が定める OAuth 2.1 フローに準拠:

```
MCP Client (Claude Desktop 等)
    │ 接続要求
    ↓
MCP Server → 401 + Protected Resource Metadata (RFC 9728)
    │
    ↓
MCP Client → ブラウザを開く → Authorization Server (Keycloak)
    │ ユーザーがログイン + 「Allow」クリック
    ↓
Keycloak → Access Token 発行（短命 JWT + PKCE）
    │
    ↓
MCP Client → Token を使って MCP Server に再接続
    │
    ↓
MCP Server → Token 検証 → ツール利用可能
```

- ユーザーはブラウザで承認ボタンを押すだけ（トークンの手動コピペ不要）
- Dynamic Client Registration (DCR) で MCP クライアントが自動登録
- 短命トークン（5-30分）+ リフレッシュトークンで安全性確保

**Authorization Server: Keycloak (OSS)**:

- MCP 公式チュートリアルで推奨
- Docker Compose に追加するだけで動作
- ユーザー登録・同意管理・トークン発行を一元管理
- Rate Limiting: Keycloak のクライアントポリシーで制御

**Transport**: Streamable HTTP（MCP 標準、Cloud Run と相性良い）

**コスト考慮**:

MCP 経由のリクエストはサーバー側で LLM API コスト（OpenAI）が発生するため:
- Keycloak で認証済みユーザーのみアクセス可能
- Rate Limiting でユーザーあたりのリクエスト数を制限
- 利用状況は Langfuse でトレーシング

**実装スコープ**:

| 項目 | 状態 |
|------|------|
| MCP Server 基盤（FastMCP + Streamable HTTP） | ストレッチ |
| OAuth 2.1 認証（Keycloak） | ストレッチ |
| ask_course_finder Tool | ストレッチ |
| search_courses / get_skill_gap / get_learning_path | ストレッチ |
| MCP 経由のパーソナライズドレコメンド | ストレッチ（追加） |

---

---

## ADR-013: API Gateway 導入 — Hono 薄いルーティング層

### Status: Accepted

### Context
キャプストーン要件に「マイクロサービス + API Gateway」パターンが含まれる。既存の API Layer（Hono）はビジネスロジックと HTTP 処理を担っており、単一エントリポイントとしての Gateway 責務を持たせると関心が混在する。将来サービスが増えた際に Gateway 修正が肥大化するリスクがある。

### Decision
**Hono を API Gateway として新設（`gateway/`）** し、既存の Backend Service（`backend/`）と明確に分離する。

```
Internet
    ↓
gateway/  (Hono, port:3000)   ← 唯一の外部公開エントリポイント
    ↓ proxy /api/*
backend/  (Hono, port:3001)   ← 内部のみ（Gateway 経由のみアクセス可）
    ↓ 内部 HTTP 呼び出し
ai/       (Python, port:8001) ← 内部のみ（Backend からのみ呼び出し）
```

**Gateway の責務（薄く保つ）**:
- CORS
- リクエストログ
- レート制限（IP ベース）
- `/api/*` → Backend Service へのプロキシ転送

**Gateway に含めないもの**: JWT 検証・ビジネスロジック・DB アクセス

**新サービス追加時**: Gateway の routes に proxy 1行追加するだけ。各サービスは独立して開発・デプロイ可能。

### Alternatives Considered

| 選択肢 | 棄却理由 |
|--------|---------|
| **既存 Hono (backend/) を Gateway に昇格** | Gateway とビジネスロジックが混在。新サービス追加時に backend/ の修正が必要になり、関心分離が崩れる |
| **Python（FastAPI）で Gateway 実装** | 授業での想定は Python 統一だが、既存 Hono 資産を活かせる。言語を増やすより既存スタックで統一するほうがメンテコストが低い |
| **GCP API Gateway** | OpenAPI spec によるルーティング定義が必要。カスタムロジック（rate_limiter 等）が書けず、実装コードがマネージドサービスに隠蔽される。「自分で設計・実装した Gateway」として説明できなくなる。設定複雑性とコードレス化のトレードオフで棄却 |
| **Kong / nginx** | OSS ミドルウェアで機能は豊富だが、設定ファイルベースで TypeScript との相性が悪い。キャプストーン規模ではオーバーキル |

### Deployment（GCP Cloud Run）

| Service | 公開設定 | 備考 |
|---------|---------|------|
| gateway | `--allow-unauthenticated` | 唯一の公開 URL |
| backend | `--no-allow-unauthenticated` | Gateway のサービスアカウントのみアクセス可 |
| ai | `--no-allow-unauthenticated` | Backend からのみ呼び出し |

### Consequences
- ✓ サービスごとに独立デプロイ・スケール可能（マイクロサービス要件を満たす）
- ✓ 新サービス追加時は Gateway に proxy 1行追加のみ。既存サービス無修正
- ✓ 全 cross-cutting concerns（CORS・ログ・レート制限）が一箇所に集約
- ✓ Backend・AI は外部から直接アクセス不可（セキュリティ向上）
- ✗ ローカル開発時にコンテナが1つ増える（gateway + backend + ai + qdrant + postgres）
- ✗ Gateway 障害が全サービスに影響（SPOF）— Cloud Run の自動再起動で緩和

---

*作成日: 2026-03-12*
*更新日: 2026-03-16*
*フレームワーク参照: FDE Architecture Decision Record (architecture_options.md)*
