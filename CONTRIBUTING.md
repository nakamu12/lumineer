# Contributing to Lumineer

Thank you for contributing! This document covers branching strategy, commit conventions, the PR process, and the mandatory development workflow.

---

## Table of Contents

- [Development Workflow](#development-workflow)
- [Branch Naming](#branch-naming)
- [Working with git worktree](#working-with-git-worktree)
- [Commits](#commits)
- [Pull Requests](#pull-requests)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)

---

## Development Workflow

Every feature or fix follows this sequence — no exceptions:

```
1. Create a GitHub Issue
2. Create a feature branch via git worktree
3. TDD: RED → GREEN → REFACTOR
4. Run tests: bun test / pytest
5. Run Code Review + Security Review (parallel subagents)
6. Push and open a PR
7. CI must pass before merge
```

### Branch flow

```
main ─────────────────────── production (auto-deploy to Cloud Run)
  └── develop ──────────────── integration target
        └── LM0001-feature/rag-hybrid_search
        └── LM0002-fix/agents-triage_routing
```

- **Never commit directly to `main` or `develop`.**
- All changes go through a feature branch → PR → CI → develop → main.

---

## Branch Naming

```
LM{IssueID}-{type}/{scope}-{detail}
```

| Element | Values |
|---------|--------|
| `LM` | Fixed prefix (Lumineer) |
| `IssueID` | 4-digit GitHub Issue number (e.g. `0042`) |
| `type` | `feature` · `fix` · `hotfix` · `refactor` · `docs` · `test` · `chore` |
| `scope` | `frontend` · `backend` · `rag` · `agents` · `data` · `infra` · `mcp` |
| `detail` | `snake_case` summary |

**Examples:**

```
LM0001-feature/rag-hybrid_search
LM0042-fix/agents-triage_routing
LM0010-feature/frontend+backend-search_results   # multi-scope: use +
LM0055-docs/infra-setup_guide
```

---

## Working with git worktree

All feature work must use `git worktree` so the main checkout always stays on `develop`.

### Worktree location

```
{project_root}/../worktree/{branch-name-with-slashes-replaced-by-dashes}/
```

Example:
- Branch: `LM0001-feature/rag-hybrid_search`
- Directory: `../worktree/LM0001-feature-rag-hybrid_search`

### Start a new feature

```bash
# From the main repo (lumineer/)
git worktree add ../worktree/LM{NNNN}-{type}-{scope}-{detail} \
  -b LM{NNNN}-{type}/{scope}-{detail} origin/develop

cd ../worktree/LM{NNNN}-{type}-{scope}-{detail}
git push -u origin LM{NNNN}-{type}/{scope}-{detail}
```

### Infrastructure during development

Keep infrastructure running from the main repo, run app services directly from the worktree:

```bash
# Main repo — start infra once and leave it running
cd lumineer && docker compose up -d   # postgres + qdrant

# Worktree — start app services directly
cd backend  && bun dev          # :3001
cd ai       && uv run python main.py  # :8001
cd gateway  && BACKEND_URL=http://localhost:3001 bun dev  # :3000
cd frontend && bun dev          # :5173
```

### Clean up after merge

```bash
git worktree remove ../worktree/{worktree_dir}
git branch -d LM{NNNN}-{type}/{scope}-{detail}
```

---

## Commits

- One commit = one logical change
- Language: English or Japanese (both OK)
- **Never commit API keys, `.env.local`, or any secrets**

Run `git diff --staged` before committing to verify no secrets are included.

---

## Pull Requests

1. **Title:** concise, under 70 characters
2. **Body:** include `Closes #IssueID` to auto-close the issue on merge
3. **CI:** all checks must pass before merging

```markdown
## Summary
- Added hybrid search (dense + sparse + RRF) to the RAG pipeline
- Exposed `RERANKER_STRATEGY` env var for strategy switching

## Test plan
- [ ] `pytest ai/tests/` passes
- [ ] Manual search returns relevant results for "Python machine learning"

Closes #42
```

---

## Code Standards

### Language policy

- **All code in English** — variable names, function names, class names, comments, docstrings, error messages
- **All UI text in English** — labels, buttons, placeholders, toasts
- **Internal docs** (requirements.md, ADRs) — Japanese OK

### TypeScript (Frontend / Backend / Gateway)

```bash
cd frontend && bun run lint && bun run typecheck
cd backend  && bun run lint && bun run typecheck
cd gateway  && bun run lint && bun run typecheck
```

Key rules:
- Use `interface` for object shapes, `type` for unions/intersections
- No `any` — use `unknown` for untrusted input, then narrow safely
- Entity creation via Factory pattern — no `new Entity()` direct calls
- External dependencies (DB, LLM, VectorDB) accessed through Ports only

### Python (AI Processing)

```bash
cd ai && ruff check . && ruff format . && mypy .
```

Key rules:
- Type annotations on all function signatures
- `@dataclass(frozen=True)` for immutable data
- Pydantic Settings for all configuration — no `os.environ` direct access
- Prompts in `prompts/*.md` — no inline strings in agent definitions

---

## Testing Requirements

All PRs must pass the full test suite:

```bash
# Frontend
cd frontend && bun test

# Backend
cd backend && bun test

# AI Processing
cd ai && pytest
```

### Test pyramid

| Layer | Tool | When |
|-------|------|------|
| Unit tests | Vitest (TS) · pytest (Python) | Every commit |
| RAG evaluation | DeepEval + Golden Dataset | LLM-related changes only |
| E2E agent tests | LLM-as-Judge | Before release |

LLM-related changes are detected by CI via path filters (`ai/app/agents/**`, `ai/app/prompts/**`, etc.). The RAG eval stage only runs for those PRs.

### TDD approach

Write failing tests **before** implementing. Follow RED → GREEN → REFACTOR:

1. **RED** — write a test that fails
2. **GREEN** — write the minimum code to make it pass
3. **REFACTOR** — clean up without breaking tests

---

## Architecture Constraints

These must be respected in every PR:

| Rule | Detail |
|------|--------|
| Layer isolation | Frontend never calls Backend or AI directly — always via Gateway |
| Dependency direction | `interfaces/ → usecases/ → ports/ ← infrastructure/` |
| No hardcoded prompts | Agent instructions must live in `prompts/*.md` |
| Port/Adapter | LLM, VectorDB, Embedding accessed through abstract Ports |
| Factory pattern | Entity creation through `*Factory.create()` — never `new Entity()` |

See [docs/adr.md](docs/adr.md) for the full set of architecture decisions.
