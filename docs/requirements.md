# Lumineer — 要件定義書

> Intelligent Course Discovery System
> FDE キャプストーンプロジェクト

---

## 1. プロジェクト概要

Coursera の公開コースデータ（6,645件）を活用し、AIエージェントによるインテリジェントなコース検索・スキル分析・学習パス生成を提供する Web アプリケーション。

**主要ユースケース**:

- コース検索: キーワード・自然言語でコースを発見
- スキルギャップ分析: 現在のスキルと目標の差分を分析し、必要なコースを提案
- 学習パス生成: 目標に向けた最適な学習順序を自動生成

---

## 2. システムアーキテクチャ

**構成**: モジュラーモノリス + Docker Compose

```
┌─────────────────────────────────────────────────────┐
│  Frontend: Bun + React (Vite) + Shadcn UI           │
│  Firebase Hosting (CDN)                              │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP (REST + SSE)
┌─────────────────────▼───────────────────────────────┐
│  API Layer: Bun + Hono (TypeScript)                  │
│  Cloud Run / クリーンアーキテクチャ                     │
│  ※ FastAPI統一案も候補として保留                       │
└────────┬────────────────────────┬───────────────────┘
         │ HTTP                   │ SQL
┌────────▼───────────────────┐  ┌▼────────────────────┐
│  AI Processing Layer       │  │  PostgreSQL          │
│  Python + Litestar         │  │  ユーザー・チャット    │
│  Cloud Run                 │  │  学習パス・設定       │
│                            │  │  Cloud SQL / Docker   │
│  ┌────────┐ ┌────────┐    │  └──────────────────────┘
│  │ Agents │ │ RAG    │    │
│  │ (SDK)  │ │Pipeline│    │
│  └────────┘ └────────┘    │
└──────────┬────────────────┘
           │
┌──────────▼──────────┐  ┌───────────────────────────┐
│  Qdrant Cloud       │  │  Observability             │
│  (VectorDB)         │  │  Langfuse + Grafana        │
└─────────────────────┘  │  + GCP Cloud Monitoring    │
                         └───────────────────────────┘
```

**設計原則**:

- **API Layer（クリーンアーキテクチャ）**: domain → infrastructure → interfaces の依存方向
- **AI Processing（OpenAI ベストプラクティス）**: agents / tools / prompts の関心分離
- Strategy パターン: リランカー、フォーマッター等を設定で切り替え可能
- Port/Adapter: LLM・VectorDB・Embedding は抽象化し差し替え可能

---

## 3. 技術スタック

| レイヤー | 技術 | 備考 |
|---------|------|------|
| Frontend | Bun + React (Vite) + Shadcn UI + Tailwind CSS | Feature-based 構成 |
| API Layer | Bun + Hono (TypeScript) | クリーンアーキテクチャ / FastAPI統一案も保留 |
| AI Processing | Python + Litestar (or FastAPI) | OpenAI ベストプラクティス |
| Agent Framework | OpenAI Agents SDK | RAGは自前実装 |
| RDB | PostgreSQL 16 (Cloud SQL + ローカル Docker) | ユーザー・チャット・学習パス・設定 |
| 認証 | JWT (jose) + bcrypt | API Layer で発行・検証 |
| VectorDB | Qdrant (Cloud + ローカル Docker) | Hybrid Search ネイティブ対応 |
| Embedding | OpenAI text-embedding-3-large (3072次元) | |
| LLM | OpenAI GPT-4o-mini | エージェント推論 + データ前処理 |
| LLMOps | Langfuse + Prometheus + Grafana + DeepEval | 全 OSS セルフホスト |
| CI/CD | GitHub Actions (Public リポジトリ) | |
| Infra | GCP Cloud Run + Firebase Hosting | 月額 ~$6 |
| MCP | Streamable HTTP (リモート接続) | 予定 |

---

## 4. API Layer 設計（Hono / TypeScript）

クリーンアーキテクチャに基づき、ドメインロジックをフレームワークから独立させる。

### ディレクトリ構成

```text
backend/src/
├── domain/                 # 核心（外部依存なし）
│   ├── entities/           #   Course, LearningPath, SkillGap
│   ├── ports/              #   LLMPort, VectorStorePort, EmbeddingPort
│   └── usecases/           #   search_courses, analyze_skill_gap, generate_learning_path
├── infrastructure/         # 外部接続の具体実装
│   ├── llm/                #   AI Processing Layer への HTTP クライアント
│   ├── vectordb/           #   Qdrant アダプタ
│   ├── embeddings/         #   text-embedding-3-large アダプタ
│   ├── reranking/          #   Strategy: None / Heuristic / CrossEncoder
│   ├── formatters/         #   Strategy: JSON / TOON
│   ├── db/                 #   PostgreSQL アダプタ（Drizzle ORM）
│   └── auth/               #   JWT 発行・検証、パスワードハッシュ
├── interfaces/             # 入力アダプタ
│   ├── api/                #   Hono REST API Router
│   └── mcp/                #   MCP Server（予定）
└── config/                 # 設定・DI
```

**依存方向**: `interfaces/ → usecases/ → ports/ ← infrastructure/`

### App Config（実行時変更可能）

| 設定 | 選択肢 | デフォルト | 変更方法 |
|------|--------|-----------|---------|
| リランカー | none / heuristic / cross-encoder | none | UI 設定画面 |
| コンテキスト形式 | JSON / TOON | json | UI 設定画面 |
| 検索件数 (top_k) | 5 / 10 / 20 | 10 | UI 設定画面 |
| 類似度閾値 | 0.5 - 0.9 | 0.7 | UI 設定画面 |

---

## 4.5 データベース設計（PostgreSQL）

ユーザー管理・チャット履歴・学習パス・設定の永続化に PostgreSQL を使用する。コース検索用の Qdrant（VectorDB）とは役割が異なり、PostgreSQL は**アプリケーションデータ**を管理する。

### データベースの役割分担

| データストア | 用途 | データ例 |
|-------------|------|---------|
| **PostgreSQL** | アプリケーションデータ（CRUD） | ユーザー、チャット履歴、学習パス、設定 |
| **Qdrant** | ベクトル検索（RAG パイプライン） | コース埋め込み、メタデータ |

### テーブル設計

```sql
-- ユーザー管理
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- チャットセッション
CREATE TABLE chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) DEFAULT 'New Chat',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- チャットメッセージ
CREATE TABLE chat_messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 学習パス
CREATE TABLE learning_paths (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    goal        TEXT,
    courses     JSONB NOT NULL DEFAULT '[]',  -- 順序付きコースリスト
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ユーザー設定（パイプライン設定）
CREATE TABLE user_settings (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reranker_strategy    VARCHAR(20) DEFAULT 'none',
    context_format       VARCHAR(10) DEFAULT 'json',
    top_k                INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
);
```

### ORM / クエリビルダー

**Drizzle ORM**（TypeScript）を API Layer で使用する。

| 観点 | Drizzle ORM | Prisma |
|------|------------|--------|
| 型安全性 | SQL-like 記法 + 完全型推論 | 独自スキーマ言語 → 型生成 |
| パフォーマンス | 薄いラッパー、SQL に近い | クライアントエンジン経由 |
| マイグレーション | SQL ベース（drizzle-kit） | 独自マイグレーション |
| バンドルサイズ | 軽量 | 重い（Rust エンジン） |

Drizzle を選んだ理由: SQL に近い記法でクリーンアーキテクチャの Port/Adapter と相性が良い。Bun との互換性も高い。

### 環境別構成

| 環境 | 構成 | 接続先 |
|------|------|--------|
| Dev | Docker Compose で PostgreSQL コンテナ | `postgres://localhost:5432/lumineer` |
| Prod | Cloud SQL (PostgreSQL) | Cloud Run → Cloud SQL Proxy |

---

## 4.6 ユーザー認証

### 認証方式: JWT（JSON Web Token）

API Layer（Hono）で JWT の発行・検証を行う。シンプルな email + password 認証。

### 認証フロー

```
1. ユーザー登録:
   POST /api/auth/register { email, password, display_name }
     → bcrypt でパスワードハッシュ化 → PostgreSQL に保存
     → JWT (Access Token + Refresh Token) を返却

2. ログイン:
   POST /api/auth/login { email, password }
     → bcrypt でパスワード照合
     → JWT (Access Token + Refresh Token) を返却

3. 認証付きリクエスト:
   GET /api/chat/sessions
   Authorization: Bearer <access_token>
     → Hono middleware で JWT 検証
     → user_id をリクエストコンテキストに注入

4. トークンリフレッシュ:
   POST /api/auth/refresh { refresh_token }
     → 新しい Access Token を返却
```

### トークン設計

| トークン | 有効期限 | 用途 |
|---------|---------|------|
| Access Token | 15 分 | API リクエスト認証 |
| Refresh Token | 7 日 | Access Token の再発行 |

### API エンドポイント

| メソッド | パス | 認証 | 説明 |
|---------|------|------|------|
| POST | `/api/auth/register` | 不要 | ユーザー登録 |
| POST | `/api/auth/login` | 不要 | ログイン |
| POST | `/api/auth/refresh` | Refresh Token | トークン再発行 |
| GET | `/api/auth/me` | 必要 | 現在のユーザー情報 |
| GET | `/api/chat/sessions` | 必要 | チャットセッション一覧 |
| POST | `/api/chat/sessions` | 必要 | 新規セッション作成 |
| GET | `/api/chat/sessions/:id/messages` | 必要 | メッセージ一覧 |
| GET | `/api/paths` | 必要 | 学習パス一覧 |
| POST | `/api/paths` | 必要 | 学習パス保存 |
| GET | `/api/settings` | 必要 | ユーザー設定取得 |
| PUT | `/api/settings` | 必要 | ユーザー設定更新 |

### Hono Middleware

```typescript
// JWT 認証ミドルウェア（interfaces/api/middleware/auth.ts）
// 1. Authorization ヘッダーから Bearer Token を取得
// 2. jose ライブラリで JWT 署名を検証
// 3. user_id をコンテキストに注入
// 4. 認証不要パス（/health, /api/auth/*）はスキップ
```

### セキュリティ要件

- パスワード: bcrypt (cost factor 12) でハッシュ化。平文保存禁止
- JWT 署名鍵: 環境変数 `JWT_SECRET` で管理（GitHub Secrets）
- HTTPS: Cloud Run はデフォルトで HTTPS 強制
- Rate Limiting: 認証エンドポイントに対するブルートフォース防止

---

## 5. AI Processing 設計（Python）

OpenAI ベストプラクティスに基づき、agents / tools / prompts を明確に分離する。
AI Processing は独立したPythonサービスとして、エージェント制御・RAG パイプライン・ガードレール・可観測性を一括管理する。

### AI Processing ディレクトリ構成

```text
ai/
├── app/                        # アプリケーション本体
│   ├── agents/                 # エージェント定義（instructions + handoffs）
│   │   ├── triage_agent.py
│   │   ├── search_agent.py
│   │   ├── skill_gap_agent.py
│   │   └── path_agent.py
│   ├── tools/                  # Tool functions（再利用可能）
│   │   ├── search_courses.py
│   │   ├── get_course_detail.py
│   │   ├── analyze_skill_gap.py
│   │   └── generate_learning_path.py
│   ├── prompts/                # プロンプトテンプレート（.md）
│   │   ├── triage.md
│   │   ├── search.md
│   │   ├── skill_gap.md
│   │   └── path.md
│   ├── guardrails/             # 5層防衛ガードレール（Section 9 参照）
│   │   ├── input/
│   │   ├── output/
│   │   └── system/
│   ├── domain/                 # 核心（外部依存なし）
│   │   ├── entities/
│   │   ├── ports/
│   │   └── usecases/
│   ├── infrastructure/         # 外部接続の具体実装
│   │   ├── llm/
│   │   ├── vectordb/
│   │   ├── embeddings/
│   │   ├── reranking/
│   │   ├── formatters/
│   │   └── ingestion/
│   ├── interfaces/             # 入力アダプタ
│   │   ├── api/
│   │   └── mcp/
│   ├── observability/          # 監視・トレーシング
│   │   ├── langfuse_tracer.py
│   │   ├── metrics.py
│   │   └── token_tracker.py
│   └── config/
│       ├── container.py        #   DI 設定
│       └── settings.py         #   Pydantic Settings
│
├── data/                       # データ管理
│   ├── raw/                    #   Coursera CSV 元データ
│   ├── processed/              #   LLM 前処理済みデータ
│   └── embeddings/             #   Qdrant snapshot / 初期化用
│
├── evals/                      # LLM 評価
│   ├── datasets/               #   Golden datasets (JSON)
│   └── benchmarks/             #   DeepEval ベンチマーク定義
│
├── scripts/                    # CLI / バッチ
│   ├── seed_data.py            #   データ初期化
│   ├── run_evals.py            #   評価実行
│   └── export_metrics.py       #   メトリクス出力
│
├── tests/                      # テスト
│
├── notebooks/                  # 実験・検証
│
├── docs/                       # ドキュメント
│
├── infra/                      # Terraform IaC
│
├── main.py                     # エントリポイント
├── pyproject.toml
└── README.md
```

### 設計方針

- **agents/**: エージェント定義（instructions + handoffs）。ビジネスロジックは持たない
- **tools/**: `@function_tool` で定義。エージェント間で再利用可能
- **prompts/**: Markdown テンプレート。コード変更なしにプロンプト調整可能
- **domain/**: エンティティ・ポート・ユースケース。外部依存なし
- **infrastructure/**: LLM・VectorDB・Embedding 等の具体実装（Port/Adapter）
- **observability/**: Langfuse トレーシング + Prometheus メトリクス + トークン追跡

### 設定管理 (Pydantic Settings)

```python
class Settings(BaseSettings):
    APP_ENV: Literal["dev", "prod"] = "dev"
    OPENAI_API_KEY: str                        # 必須
    QDRANT_URL: str = "http://qdrant:6333"     # Dev デフォルト
    QDRANT_API_KEY: str | None = None          # Prod で必須
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    RERANKER_STRATEGY: Literal["none", "heuristic", "cross-encoder"] = "none"
    CONTEXT_FORMAT: Literal["json", "toon"] = "json"
```

- Dev: デフォルト値で動作（OPENAI_API_KEY のみ必須）
- Prod: `APP_ENV=prod` で追加バリデーション（QDRANT_API_KEY 必須等）

---

## 6. フロントエンド設計

### 構成: Feature-based + lib/

```
frontend/src/
├── lib/                     # 共通 UI パーツ
│   ├── ui/                  #   Shadcn UI コンポーネント
│   ├── layout/              #   Header, PageLayout
│   ├── hooks/               #   useApi, useDebounce
│   └── types/               #   共通型定義
├── features/                # ドメイン別機能
│   ├── search/              #   コース検索
│   ├── recommend/           #   推薦・学習パス
│   └── chat/                #   チャット UI
└── app/                     # エントリポイント・ルーティング
```

### 画面構成

| 画面 | パス | 認証 | 役割 |
|------|------|------|------|
| Home | `/` | 不要 | ランディング。価値提案 + クイックスタート + 人気コース |
| Login | `/login` | 不要 | ログイン / ユーザー登録 |
| Explore | `/explore` | 不要 | コースカタログ。検索バー + フィルタ + カードグリッド + AI 要約 |
| Chat | `/chat` | 必要 | AI 対話。検索・スキル分析・推薦（会話履歴の保存に認証が必要） |
| My Path | `/path` | 必要 | 学習パス管理・可視化 |
| Course Detail | `/course/:id` | 不要 | コース詳細 |
| Settings | `/settings` | 必要 | パイプライン設定（リランカー、フォーマット等）の UI 変更 |

### デザイン原則

- ミニマル: 余白を活かし、情報密度を抑える
- 段階的開示: 最初は最低限、展開で詳細
- レスポンシブ: Tailwind CSS breakpoints

---

## 7. RAG パイプライン

### 全体フロー

```
Ingestion（初回のみ）:
  CSV → LLM前処理(GPT-4o-mini) → Embedding(text-embedding-3-large) → Qdrant

検索（リクエストごと）:
  Query
    ↓
  Step 1: メタデータフィルタ（Level, Organization, rating 等）
    ↓
  Step 2: Hybrid Search（Dense + Sparse 並列）
    ↓
  Step 3: RRF（Reciprocal Rank Fusion）でスコア統合 → top_k=20
    ↓
  Step 4: Reranking（Strategy パターンで切替）
    ↓
  Step 5: Result Selection（Top-k + Threshold）
    ↓        件数不足時 → Corrective RAG（クエリ再構成→再検索）
    ↓
  Step 6: Context Assembly（JSON or TOON フォーマット）
    ↓
  Agent に返却 → LLM が回答生成
```

### 7.1 データ前処理 (Ingestion)

- **方式**: GPT-4o-mini で検索用テキスト生成（Skills 補完 + Description 正規化）
- **コレクション**: 単一コレクション + メタデータフィルタ
- **前処理コスト**: ~$1.10（1回きり）

### 7.2 Embedding

- **モデル**: OpenAI `text-embedding-3-large`（3072次元）
- **コスト**: $0.26（6,645件、1回きり）
- **ストレージ**: ~80MB（Qdrant Cloud 無料枠 1GB に十分収まる）

### 7.3 Hybrid Search

- **Dense**: text-embedding-3-large によるベクトル類似度（意味検索）
- **Sparse**: Qdrant Sparse Vector によるキーワードマッチ（BM25 相当）
- **スコア統合**: RRF（順位ベース統合、正規化不要、Qdrant ネイティブ対応）
- **クエリ最適化**: Search Agent の instructions で Corrective RAG パターンを実行

### 7.4 メタデータフィルタリング

**Qdrant payload スキーマ**:

| フィールド | 型 | フィルタ種別 | 用途 |
|-----------|-----|------------|------|
| `level` | string | 完全一致 | 難易度（Beginner/Intermediate/Advanced） |
| `organization` | string | 完全一致 / match_any | 提供組織 |
| `rating` | float | 範囲（≥ N） | 高評価フィルタ |
| `skills` | list[string] | match_any | スキル絞り込み |
| `enrolled` | int | 範囲 | 人気度 |
| `num_reviews` | int | 範囲 | 信頼性 |
| `title` | string | 表示用 | LLM コンテキスト |
| `description` | string | 表示用 | LLM コンテキスト |
| `url` | string | 表示用 | フロントエンドリンク |
| `modules` | string | 表示用 | コース構成情報 |
| `schedule` | string | 表示用 | 所要時間 |
| `instructor` | string | 表示用 | 講師名 |

**欠損データ**:
- Level 欠損（778件/12%）: フィルタ時、欠損も結果に含める
- Skills 空（1,954件/29%）: LLM 前処理で補完済み

**Search Agent ツール**:

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

### 7.5 リランキング（Strategy パターン）

3 つの Strategy を Golden Dataset で比較評価し、コストに見合う精度向上があるかを判断:

| Strategy | 手法 | コスト | レイテンシ |
|----------|------|--------|-----------|
| `none` | パススルー（ベースライン） | $0 | 0ms |
| `heuristic` | `α × relevance + β × rating + γ × enrolled` | $0 | ~1ms |
| `cross-encoder` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | $0 | +200-500ms |

```python
class BaseReranker:
    def rerank(self, query: str, results: list[dict], top_k: int) -> list[dict]:
        raise NotImplementedError

class NoReranker(BaseReranker):        # パススルー
class HeuristicReranker(BaseReranker):  # 重み付きスコア
class CrossEncoderReranker(BaseReranker): # Neural Re-ranking
```

切り替え: 環境変数 `RERANKER_STRATEGY` or UI 設定画面

### 7.6 Result Selection

- **Top-k**: リランキング後の上位 k 件を返却（デフォルト k=10）
- **Threshold**: 類似度スコアが閾値未満の結果を除外（閾値は Golden Dataset で調整）
- **件数不足時**: Search Agent が Corrective RAG パターンでクエリ再構成→再検索

### 7.7 コンテキスト組み立て（Formatter）

JSON / TOON 切り替え可能なマイクロモジュール:

| 形式 | トークン消費 | 特徴 |
|------|------------|------|
| JSON | 多い（キー名×件数） | LLM 理解度が確実 |
| TOON | **約50%削減** | 同じ予算でより多くの結果を含められる |

**TOON (Token-Oriented Object Notation)**:

```
courses[3]{title,org,level,rating,enrolled,skills}:
  ML Specialization,Stanford,Beginner,4.8,12345,"Python, TensorFlow"
  Deep Learning,DeepLearning.AI,Intermediate,4.9,8901,"Neural Networks, CNN"
  NLP Specialization,DeepLearning.AI,Advanced,4.7,5432,"NLP, Transformers"
```

- ToonFormatter: 1ファイル、外部依存なし、Pure Python
- 不要時はファイル削除 + Formatter 差し替えで完全除去可能
- 切り替え: 環境変数 `CONTEXT_FORMAT` or UI 設定画面

**Hallucination 防止**: Search Agent instructions に以下を明記:
- 検索結果に含まれるコースのみ紹介
- 結果にないコースを推薦・創作しない
- データ値（rating, level 等）は検索結果を正確に引用

---

## 8. エージェントアーキテクチャ

### Triage パターン（4 エージェント）

```
                ┌─────────────┐
   ユーザー入力 → │ Triage Agent │ ← 入力を分類・ルーティング
                └──────┬──────┘
                       │ handoff()
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌─────────────┐ ┌──────────┐ ┌──────────┐
   │ Search Agent │ │ Skill Gap│ │ Path     │
   │ コース検索   │ │ スキル分析│ │ 学習パス  │
   └─────────────┘ └──────────┘ └──────────┘
```

| エージェント | 役割 | 入力例 |
|-------------|------|--------|
| Triage Agent | 分類・ルーティング | 全てのユーザー入力 |
| Search Agent | コース検索・フィルタリング | 「Python 初心者 コース」 |
| Skill Gap Agent | スキル比較・ギャップ分析 | 「データサイエンティストになるには？」 |
| Path Agent | 学習パス生成・最適化 | 「3ヶ月で Web 開発を学ぶプラン」 |

### 統一 AI バックエンド

Explore 検索バーと Chat 画面は**同じ Triage Agent** を呼ぶ。違いは出力フォーマットのみ:
- Explore: AI 要約パネル + コースカードグリッド（Google 風）
- Chat: 会話形式 + インラインカード

---

## 9. ガードレール設計（5層防衛アーキテクチャ）

授業で学んだ **Fortress Model（5層防衛）** をベースに、Lumineer の特性に合わせた多層ガードレールを設計する。OpenAI Agents SDK の `@input_guardrail` / `@output_guardrail` デコレータによる並列実行で、レイテンシ影響を最小化。

### 設計原則

- **多層防御 (Defense-in-Depth)**: 単一層の突破がシステム全体の侵害に繋がらない
- **フェイルセーフ**: 判定が曖昧な場合は拒否（安全側に倒す）
- **観測可能**: 全ガードレールのトリガーを Langfuse にログ
- **テスト可能**: 各ガードレールに対する Red Team テストケースを Golden Dataset に含む

### L1: 入力ガード（Input Guards）

| ガードレール | 実装方式 | 説明 |
|---|---|---|
| **プロンプトインジェクション検出** | `@input_guardrail` + LLM 判定 | 「Ignore previous instructions」等のシステム指示上書きを検出・ブロック |
| **Toxicity 検出** | `@input_guardrail` + LLM 判定 | 暴言・脅迫・差別表現のブロック |
| **Off-topic 検出** | `@input_guardrail` + LLM 判定 | コース検索・大学教育と完全に無関係なリクエストを検出（グレーゾーンは許容） |
| **PII マスキング（入力側）** | Microsoft Presidio `mask()` | LLM に送信する前に個人情報をプレースホルダーに置換 |

**Off-topic 境界**:
- ブロック: 「今日の天気は？」「レシピ教えて」等、明確に無関係な質問
- 許容: 「データサイエンスのキャリアパスは？」「この資格は就職に有利？」等、学習・教育に関連するグレーゾーン

**PII 検出対象**: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD（日本の電話番号パターン対応）

### L2: データ/メモリ層ガード（Data Guards）

| ガードレール | 実装方式 | 説明 |
|---|---|---|
| **Context Window 保護** | tiktoken トークンカウント + 切り詰め | RAG パイプライン内でトークン予算管理（7.7 節と統合） |
| **RAG データ検証** | スコアしきい値 + ソース検証 | 類似度が閾値未満の低品質検索結果を除外（7.6 節 Result Selection と統合） |

### L3: エージェント層ガード（Agent Guards）

| ガードレール | 実装方式 | 説明 |
|---|---|---|
| **Tool Permission Scoping** | 各 Agent の `tools` 定義で制限 | Search Agent は `search_courses` のみ等、最小権限原則 |
| **Identity / Persona Lock** | System Prompt に明示 + 出力検証 | 各エージェントが役割を逸脱しない制約（例: Search Agent が医療アドバイスしない） |
| **ループ検出** | ターン数上限 + Handoff 回数制限 | Agent 間の無限ループ・再帰的推論ループを防止 |

### L4: 出力ガード（Output Guards）

| ガードレール | 実装方式 | 説明 |
|---|---|---|
| **ハルシネーション検出（DB照合）** | 検索結果 Set との比較 | LLM 出力に含まれるコース名が検索結果に存在するか検証（コスト0）。データ更新時は Qdrant フィルタ検索でフォールバック |
| **ハルシネーション検出（LLM Verifier）** | `@output_guardrail` + LLM 判定 | コンテキスト忠実性の汎用チェック（検索結果にない情報を付け加えていないか検証） |
| **プライバシー保護** | `@output_guardrail` + LLM 判定 | 内部 ID・システムメタデータ・Qdrant ペイロードの生データ露出を防止 |
| **PII 復元（出力側）** | Presidio `unmask()` | LLM 応答後にマスクした PII を元に復元してユーザーに返却 |

**ハルシネーション検出の 2 段構成**:
```
LLM 出力
  ↓
Stage 1: DB 照合（検索結果 Set 比較、コスト 0、レイテンシ ~0ms）
  → 出力に含まれるコース名を抽出 → retrieved_courses との差分 = 捏造
  → データ変更が疑われる場合は Qdrant フィルタ検索（~5-10ms）
  ↓
Stage 2: LLM Verifier（@output_guardrail、並列実行）
  → 「この回答はコンテキストに基づいているか」を別 LLM で検証
```

### L5: 経済層ガード（Economic Guards）

| ガードレール | 実装方式 | 説明 |
|---|---|---|
| **トークン使用量制限** | リクエスト単位の上限設定 | 1 リクエストあたりの最大入出力トークン数を制限 |
| **レート制限** | FastAPI middleware / Keycloak | ユーザーあたりのリクエスト数/分を制限 |
| **コスト追跡** | Langfuse callbacks | リクエスト毎のトークン消費・コストをログし、異常検知 |
| **ループ防止（Early-stop）** | Corrective RAG 再試行上限 | 再検索ループの最大回数を制限（Denial-of-Wallet 防止） |

### ガードレール ディレクトリ構成

```text
app/guardrails/
├── input/
│   ├── injection_detector.py    # プロンプトインジェクション検出
│   ├── toxicity_filter.py       # 有害言語フィルタ
│   ├── offtopic_detector.py     # Off-topic 検出
│   └── pii_sanitizer.py         # PII マスキング（Presidio）
├── output/
│   ├── hallucination_checker.py # DB照合 + LLM Verifier
│   ├── privacy_filter.py        # プライバシー保護
│   └── pii_restorer.py          # PII 復元
└── system/
    ├── rate_limiter.py           # レート制限
    └── cost_tracker.py           # コスト追跡
```

---

## 10. テスト戦略

### 3 層テスト構成

```
Layer 1: Unit Tests（pytest） — 毎コミット
  → Formatter, Reranker, メタデータフィルタ等の関数テスト

Layer 2: RAG Evaluation（DeepEval + Golden Dataset） — LLM 関連変更時のみ
  → 検索パイプライン品質、Strategy 比較

Layer 3: E2E Agent Tests（LLM-as-Judge） — リリース前 / 手動
  → エージェント応答品質
```

### Golden Dataset（80-100件）

| カテゴリ | 件数 | 内容 |
|---------|------|------|
| Search 系（手動） | 10件 | キーワード・自然言語検索 |
| SkillGap 系（手動） | 5件 | スキルギャップ分析 |
| Path 系（手動） | 5件 | 学習ロードマップ |
| フィルタ組み合わせ（手動） | 5件 | Level × Organization 等 |
| エッジケース（手動） | 5件 | 存在しないトピック、曖昧クエリ |
| LLM 逆生成 | 50-70件 | 実在コース→クエリを自動生成 |

### 評価メトリクス

```
Tier 1（必須 — CI/CD ゲート）:
  ├── Hit Rate@10     — 正解コースが top-10 に含まれるか
  ├── Hallucination   — 存在しないコースの創作を検知
  └── Faithfulness    — コンテキスト情報のみの正確な引用

Tier 2（Strategy 比較用）:
  ├── MRR             — 正解コースの順位
  └── NDCG@10         — ランキング品質

Tier 3（改善指針）:
  ├── Precision@10    — 検索結果のノイズ量
  └── Answer Relevancy — 応答の的確さ
```

### Strategy 比較計画

- Reranker: none vs heuristic vs cross-encoder → MRR, NDCG@10
- Formatter: JSON vs TOON → Faithfulness, Answer Relevancy + トークン消費量

---

## 11. CI/CD パイプライン

### GitHub Actions（Public リポジトリ）

```
Push / PR
    ↓
Stage 1: Lint + Unit Test（全 Push）
  → ruff + pytest
    ↓
Stage 2: LLM Eval（LLM 関連変更時のみ — paths フィルタ）
  → DeepEval + Golden Dataset
  → Tier 1 閾値未満 → マージブロック
    ↓
Stage 3: Deploy（main マージ後）
  → Docker build → Cloud Run デプロイ
```

### paths フィルタ（Stage 2 トリガー条件）

```yaml
on:
  pull_request:
    paths:
      - 'src/agents/**'
      - 'src/rag/**'
      - 'src/search/**'
      - 'src/reranking/**'
      - 'src/formatters/**'
      - 'config/prompts/**'
      - 'config/models.*'
```

フロントエンド・ドキュメント変更では LLM Eval は走らない。

### セキュリティ（Public リポジトリ）

| 保護対象 | 対策 |
|---------|------|
| API キー | GitHub Secrets |
| デプロイ URL / GCP プロジェクト ID | GitHub Secrets |
| デプロイ済みサービス | Cloud Run `--no-allow-unauthenticated` |
| デモ時 | Bearer Token 方式で審査員にトークン提供 |

---

## 12. 環境設定・シークレット管理

### ファイル構成

| ファイル | 用途 | Git 管理 |
|---------|------|---------|
| `docker-compose.yml` | Dev 用（docker compose up でそのまま動く） | Yes |
| `docker-compose.prod.yml` | Prod バックアップ（VM デプロイ用、当面未使用） | Yes |
| `Dockerfile` | イメージビルド（Dev / Prod 共通） | Yes |
| `.env.local` | Dev の API キーのみ | No (.gitignore) |
| `.env.example` | 設定項目一覧（値は空） | Yes |

### Dev 環境

```bash
git clone → echo "OPENAI_API_KEY=sk-xxx" > .env.local → docker compose up
```

- ローカル Qdrant + PostgreSQL コンテナが起動（外部サービス依存なし、OpenAI API 以外）
- デフォルト値で全て動作

### Prod 環境

```bash
# CI/CD が実行（開発者は何もしない）
gcloud run deploy app \
  --set-env-vars "APP_ENV=prod" \
  --set-env-vars "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" \
  --set-env-vars "QDRANT_URL=${{ secrets.QDRANT_URL }}" \
  --set-env-vars "QDRANT_API_KEY=${{ secrets.QDRANT_API_KEY }}" \
  --set-env-vars "DATABASE_URL=${{ secrets.DATABASE_URL }}" \
  --set-env-vars "JWT_SECRET=${{ secrets.JWT_SECRET }}"
```

- .env ファイルは存在しない
- GitHub Secrets → Cloud Run 環境変数に直接注入

---

## 13. Git・タスク管理

### ブランチ構成

```
main ─────────── 本番（Cloud Run 自動デプロイ）
  │
  └── develop ── 統合（feature 統合先）
        │
        └── LM0001-feature/rag-hybrid_search
```

### ブランチ命名規則

```
{prefix}{kanbanID}-{type}/{scope}-{detail}
```

- **prefix**: `LM`（Lumineer）
- **kanbanID**: 4桁 Issue 番号
- **type**: feature / fix / hotfix / refactor / docs / test / chore
- **scope**: frontend / backend / rag / agents / data / infra / mcp
- **detail**: snake_case の内容要約

例: `LM0001-feature/rag-hybrid_search`, `LM0010-feature/frontend+backend-search_results`

### フロー

```
通常:   develop → feature branch → PR → CI → develop → main
hotfix: main → hotfix branch → PR → main + develop マージ
```

### タスク管理

- **GitHub Issues**: 全タスクを Issue で採番
- **GitHub Projects**: カンバン（Backlog → To Do → In Progress → Review → Done）
- **PR に `Closes #N`**: マージ時に Issue 自動クローズ + カンバン自動移動

---

## 14. LLMOps・モニタリング

### 3 層オブザーバビリティ

| ツール | 役割 | 形態 |
|--------|------|------|
| Langfuse | LLM トレーシング（プロンプト入出力、トークン消費、コスト） | Docker 常駐 |
| Prometheus + Grafana | メトリクス収集・ダッシュボード（レイテンシ、エラー率） | Docker 常駐 / Cloud Run |
| DeepEval | RAG 品質評価（Golden Dataset） | バッチ実行 |

### 環境別構成

| ツール | Dev（ローカル） | Prod |
|--------|----------------|------|
| メトリクス | Prometheus (Docker) | GCP Cloud Monitoring |
| ダッシュボード | Grafana (Docker) | Grafana (Cloud Run) |
| LLM トレーシング | Langfuse (Docker) | ローカルのみ or Langfuse Cloud 無料枠 |
| RAG 評価 | DeepEval (pip) | ローカルのみ |

---

## 15. インフラ・デプロイ

### 本番構成（GCP）

| サービス | ホスティング | 月額 |
|---------|------------|------|
| Frontend | Firebase Hosting (CDN) | $0 |
| API Layer | Cloud Run | $0~$1 |
| AI Processing | Cloud Run | $0~$2 |
| RDB | Cloud SQL (PostgreSQL) 無料枠 or 最小インスタンス | $0~$9 |
| Grafana | Cloud Run (Provisioning as Code) | $0 |
| VectorDB | Qdrant Cloud (無料枠 1GB) | $0 |
| メトリクス | GCP Cloud Monitoring | $0 |
| LLM API | OpenAI GPT-4o-mini | ~$5 |
| Embedding | OpenAI text-embedding-3-large | ~$1 |
| **合計** | | **~$6〜$15/月** |

### コールドスタート対策

- API (Hono/Bun): ~1-2秒
- AI Processing (Python): ~5-15秒
- デモ時: `min-instances=1` or 事前ウォームアップ

---

## 16. MCP Server（ストレッチ目標）

**位置づけ**: ストレッチ目標。本体と疎結合であり、実装しなくても本体に影響なし。

**目的**: ユーザーが自分の AI ツール（Claude Desktop, Cursor, VS Code 等）から MCP 経由でコース検索を利用可能にする。LLM 推論はサーバー側で完結するため、ユーザー側に OpenAI API キーが不要。

**アーキテクチャ**:

```
Web UI (Explore/Chat) ──→ ┐
                           ├→ Triage Agent → 同じ RAG パイプライン → 回答
MCP Client            ──→ ┘
```

入口が違うだけで、パイプラインは完全共有。`interfaces/mcp/` に配置。

**公開する MCP Tools**:

| Tool | 用途 | サーバー側処理 |
|------|------|--------------|
| `ask_course_finder` | 自然言語クエリ（メイン） | Triage Agent が全て処理 |
| `search_courses` | フィルタ付きコース検索 | 検索パイプラインのみ |
| `get_skill_gap` | スキルギャップ分析 | SkillGap Agent |
| `get_learning_path` | 学習パス生成 | Path Agent |

**認証認可: OAuth 2.1（MCP 公式標準）**:

```
MCP Client → 接続 → MCP Server (401) → ブラウザ開く → Keycloak
→ ユーザーがログイン + 「Allow」クリック → JWT 発行 → アクセス可能
```

| 項目 | 仕様 |
|------|------|
| Transport | Streamable HTTP |
| 認証 | OAuth 2.1 + PKCE（MCP 公式標準） |
| Authorization Server | Keycloak (OSS, Docker) |
| クライアント登録 | Dynamic Client Registration (DCR) |
| トークン | 短命 JWT（5-30分）+ リフレッシュトークン |
| Rate Limiting | Keycloak クライアントポリシーで制御 |
| デプロイ | Cloud Run 内（AI Processing と同居） |

**ユーザー体験**:

```json
// Claude Desktop / VS Code の設定に追加するだけ
{
  "mcpServers": {
    "course-finder": {
      "url": "https://course-finder-xxx.run.app/mcp"
    }
  }
}
// → 初回接続時にブラウザが開き、承認ボタンを押すだけ
```

---

## 17. AI Rules

`.claude/CLAUDE.md` にプロジェクトルールを定義し、AI アシスタントが ADR やブランチ命名規則を理解した状態で開発を支援。サンプルをベースに作成。

---

## 付録: データ仕様

### Coursera データセット

- **件数**: 6,645 コース
- **ファイル**: coursera.parquet (11.4MB)

| カラム | 型 | 欠損率 | 備考 |
|--------|-----|--------|------|
| Title | string | 0% | コース名 |
| Description | string | 0% | 平均 3,198 文字、最大 32,804 文字 |
| Skills | string (JSON list) | 29% | LLM 前処理で補完 |
| Level | string | 12% (778件) | Beginner / Intermediate / Advanced / None |
| Organization | string | 0% | 提供組織 |
| Rating | string | 0% | float に変換して使用 |
| Enrolled | string | 0% | int に変換して使用 |
| Modules/Courses | string | | コース構成 |
| Schedule | string | | 所要時間 |
| URL | string | | Coursera リンク |
| Instructor | string | | 講師名 |

---

*作成日: 2026-03-13*
*参照: ADR-001 〜 ADR-012 (code/capstone/docs/adr.md)*
