---
description: Public リポジトリ向けセキュリティルール
---

# Security Rules

## Public リポジトリ鉄則

- **API Key はコードに含めない**。GitHub Secrets 経由で注入
- `.env.local` は `.gitignore` に含める（Dev 用 API Key）
- `.env.example` に設定項目一覧を記載（値は空）
- コミット前に `git diff --staged` でシークレット混入を確認

## 環境変数管理

```python
# ✅ Pydantic Settings で管理
class Settings(BaseSettings):
    OPENAI_API_KEY: str
    QDRANT_API_KEY: str | None = None

# ❌ ハードコード禁止
api_key = "sk-xxx"
```

- Dev: `.env.local` + デフォルト値で動作（OPENAI_API_KEY のみ必須）
- Prod: GitHub Secrets → Cloud Run 環境変数に直接注入。.env ファイルは存在しない

## Prod デプロイ

- Cloud Run: `--no-allow-unauthenticated` でデフォルト非公開
- デモ時: Bearer Token 方式で審査員にトークン提供
- GCP プロジェクト ID も GitHub Secrets に格納

## 入出力保護

- PII マスキング: Presidio で LLM 送信前にマスク、応答後に復元
- 内部 ID・システムメタデータの露出防止
- Qdrant payload の生データをフロントエンドに返さない
