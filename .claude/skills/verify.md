---
description: "Run full verification suite (lint + typecheck + test) across all layers. Usage: /verify [layer]"
user_invocable: true
---

# Verify

Run the complete verification suite to ensure code quality before committing or creating a PR.

## Target

If $ARGUMENTS specifies a layer (frontend, backend, gateway, ai, all), verify that layer.
Otherwise, verify all layers.

## Verification Steps

### 1. Frontend
```bash
cd frontend && bun run lint && bun run typecheck && bun test
```

### 2. Backend
```bash
cd backend && bun run lint && bun run typecheck && bun test
```

### 3. Gateway
```bash
cd gateway && bun run lint && bun run typecheck
```

### 4. AI Processing
```bash
cd ai && ruff format --check . && ruff check . && mypy . && pytest
```

## Run Order

1. Run lint + typecheck for all layers in parallel (fast feedback)
2. Run tests for all layers in parallel
3. Report results

## Output Format

```
Layer       | Lint | Types | Tests
------------|------|-------|------
Frontend    |  ✓   |   ✓   |  ✓  (12 passed)
Backend     |  ✓   |   ✓   |  ✓  (8 passed)
Gateway     |  ✓   |   ✓   |  -
AI          |  ✓   |   ✓   |  ✓  (24 passed)

Result: ALL PASSED ✓
```

If any step fails, show the error details and suggest fixes.

## Pre-PR Checklist

After verification passes:
- [ ] All lint/typecheck/test pass
- [ ] No `console.log` or `print()` in production code
- [ ] No secrets in staged files
- [ ] Commit messages are clean (no `wip:` prefix)
- [ ] Branch name follows `LM{ID}-{type}/{scope}-{detail}` pattern
