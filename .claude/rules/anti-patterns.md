---
description: このプロジェクトで避けるべきアンチパターン集
---

# Anti-Patterns

## 1. レイヤー貫通: Frontend → AI Processing 直接呼び出し

```typescript
// ❌ Frontend から AI Processing を直接呼ぶ
const res = await fetch("http://ai-processing:8000/agents/search", { body });

// ✅ 必ず API Layer を経由する
const res = await fetch("/api/search", { body });
```

## 2. 依存方向の逆転: domain/ が infrastructure/ に依存

```python
# ❌ domain 層が具体実装に依存
from app.infrastructure.vectordb.qdrant_client import QdrantClient

class SearchCoursesUseCase:
    def __init__(self):
        self.client = QdrantClient()  # 具体実装を直接参照

# ✅ Port を介して抽象に依存
from app.domain.ports.vector_store import VectorStorePort

class SearchCoursesUseCase:
    def __init__(self, vector_store: VectorStorePort):
        self.vector_store = vector_store  # DI で注入
```

## 3. Agent にビジネスロジックを書く

```python
# ❌ Agent 定義内でフィルタリングや加工を実装
search_agent = Agent(
    name="Search Agent",
    instructions="検索結果を rating > 4.0 でフィルタし、enrolled 降順でソートして...",
    tools=[raw_qdrant_search],  # 生の検索結果を返す Tool
)

# ✅ Agent はルーティングのみ。ロジックは Tool 内で完結
search_agent = Agent(
    name="Search Agent",
    instructions=open("app/prompts/search.md").read(),
    tools=[search_courses],  # フィルタ・ソート済みの結果を返す Tool
)
```

## 4. プロンプトのハードコード

```python
# ❌ instructions をコード内に直書き
triage_agent = Agent(
    instructions="あなたはコース検索アシスタントです。ユーザーの入力を分類し..."
)

# ✅ prompts/*.md から読み込む
triage_agent = Agent(
    instructions=open("app/prompts/triage.md").read()
)
```

## 5. Tool Permission の過剰付与

```python
# ❌ 全 Agent に全 Tool を付与
search_agent = Agent(
    tools=[search_courses, analyze_skill_gap, generate_learning_path, get_course_detail]
)

# ✅ 最小権限: 各 Agent は必要な Tool のみ
search_agent = Agent(
    tools=[search_courses, get_course_detail]  # 検索に必要なものだけ
)
```

## 6. API Key のハードコード / コミット

```python
# ❌ コードに直書き
client = OpenAI(api_key="sk-proj-xxxxxxxxxxxx")

# ❌ .env をコミット
# .env に OPENAI_API_KEY=sk-xxx を書いて git add .env

# ✅ Pydantic Settings 経由で取得
from app.config.settings import get_settings
settings = get_settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)
# Dev: .env.local（.gitignore 対象）  Prod: GitHub Secrets → Cloud Run 環境変数
```

## 7. PII を未マスクで LLM に送信

```python
# ❌ ユーザー入力をそのまま LLM に渡す
response = agent.run("山田太郎です。taro@example.com のメールで...")

# ✅ Presidio で PII をマスクしてから送信
masked = pii_sanitizer.mask(user_input)   # <PERSON>, <EMAIL> に置換
response = agent.run(masked)
output = pii_restorer.unmask(response)     # 応答後に復元
```

## 8. Qdrant クライアントの infrastructure/ 外からの直接利用

```python
# ❌ Tool や usecase から Qdrant を直接呼ぶ
from qdrant_client import QdrantClient

@function_tool
def search_courses(query: str) -> str:
    client = QdrantClient(url="http://qdrant:6333")
    results = client.search(...)

# ✅ Port/Adapter 経由でアクセス
@function_tool
def search_courses(query: str) -> str:
    vector_store = container.resolve(VectorStorePort)
    results = vector_store.hybrid_search(query=query, limit=10)
```

## 9. Context Window を無視した全件コンテキスト注入

```python
# ❌ 検索結果を全フィールド・大量件数でそのまま注入
results = vector_store.search(query, limit=100)
context = json.dumps([r.payload for r in results])  # 全 payload を丸ごと

# ✅ top_k + Formatter で必要最小限のコンテキストに整形
results = vector_store.hybrid_search(query, limit=10)
selected = result_selector.apply(results, threshold=0.7)
context = formatter.format(selected)  # JSON or TOON で整形
```

## 10. エンティティの直接生成 (Factory 未使用)

```typescript
// ❌ new で直接生成
const course = new Course({ title: "ML", rating: 4.8 });

// ✅ Factory パターンでバリデーション付き生成
const course = CourseFactory.create({ title: "ML", rating: 4.8 });
```

## 11. ハルシネーション検証の省略

```python
# ❌ LLM 出力をそのままユーザーに返す
response = agent.run(user_query)
return response.output  # 存在しないコースを推薦している可能性

# ✅ DB 照合 + LLM Verifier の 2 段チェック
response = agent.run(user_query)
# Stage 1: 出力に含まれるコース名を retrieved_courses と照合
# Stage 2: @output_guardrail で LLM Verifier 検証
# 両方パスした場合のみ返却
```

## 12. Golden Dataset なしの LLM 変更

```bash
# ❌ プロンプトや RAG パイプラインを変更して、手動確認だけでマージ
git commit -m "プロンプト改善"
git push

# ✅ 変更前後で Golden Dataset 評価を実行し、メトリクスを比較
uv run python scripts/run_evals.py  # Hit Rate, Faithfulness, Hallucination
# Tier 1 メトリクスが閾値を満たすことを確認してからマージ
```
