---
description: AI Processing Layer (Python) の OpenAI ベストプラクティスルール
globs: ai/**
---

# AI Processing Rules

## 関心分離の原則

```
agents/  → エージェント定義（instructions + handoffs のみ）
tools/   → @function_tool で定義。ビジネスロジックの実行単位
prompts/ → Markdown テンプレート。コード変更なしに調整可能
```

- Agent にビジネスロジックを書かない。Tool を呼ぶだけ
- Tool は再利用可能な単位で設計。エージェント間で共有できる
- プロンプトは `prompts/*.md` に外部化（コード内文字列禁止）

## Python コーディング規約

- **ランタイム**: Python 3.12+
- **パッケージ管理**: `uv` (pyproject.toml)
- **Lint**: `ruff check .` + `ruff format .`
- **型チェック**: `mypy .`
- **設定**: Pydantic Settings (`config/settings.py`)

```python
# ✅ 型ヒント必須
def search_courses(query: str, limit: int = 10) -> list[CourseEntity]:
    ...

# ❌ 型ヒントなし
def search_courses(query, limit=10):
    ...
```

## エントリポイント

```python
# main.py — サーバー起動のみ
import uvicorn
from app.interfaces.api.routes import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 設定管理

```python
# ✅ Pydantic Settings で一元管理
from app.config.settings import get_settings
settings = get_settings()

# ❌ os.environ 直接参照
import os
api_key = os.environ["OPENAI_API_KEY"]
```

## Observability

- 全 Agent 呼び出しを Langfuse でトレース
- Prometheus メトリクス: レイテンシ、エラー率、トークン消費
- `observability/token_tracker.py` でリクエスト毎のコストを記録

## ディレクトリ配置ルール

- エンティティ定義 → `domain/entities/`
- ポート（抽象） → `domain/ports/`
- ユースケース → `domain/usecases/`
- 外部 API 実装 → `infrastructure/`
- API ルート → `interfaces/api/`
- DI 設定 → `config/container.py`
