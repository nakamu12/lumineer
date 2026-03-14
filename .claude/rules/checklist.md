---
description: 開発完了チェックリスト
---

# Development Checklist

## Language

- [ ] Code is in English: variable names, function names, class names, comments, docstrings
- [ ] UI text is in English: labels, buttons, placeholders, error messages
- [ ] No Japanese in source code (except internal docs like requirements.md, ADR)

## コード品質

- [ ] Factory パターンでエンティティ生成しているか（`new Entity()` 禁止）
- [ ] Port/Adapter で外部依存を抽象化しているか
- [ ] プロンプトは `prompts/*.md` に外部化されているか
- [ ] 環境変数は Pydantic Settings / process.env 経由か（ハードコード禁止）
- [ ] API Key がコードやコミットに含まれていないか

## テスト

- [ ] Unit Test が追加/更新されているか
- [ ] 既存テストが壊れていないか（`pytest` / `bun test`）
- [ ] LLM 関連変更の場合: Golden Dataset で評価したか

## Lint & Type Check

- [ ] Python: `ruff check .` + `ruff format .` + `mypy .` がパスするか
- [ ] Frontend: `bun run lint` + `bun run typecheck` がパスするか

## ドキュメント

- [ ] 新しいパターンや設計判断は ADR に記録したか（`docs/adr.md`）
- [ ] 新しい環境変数は `.env.example` に追加したか

## PR

- [ ] ブランチ名が `LM{ID}-{type}/{scope}-{detail}` 形式か
- [ ] PR 本文に `Closes #{IssueID}` を含んでいるか
- [ ] CI が全てパスしているか
