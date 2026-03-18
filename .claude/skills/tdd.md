---
description: "Test-driven development workflow: RED → GREEN → REFACTOR. Usage: /tdd <feature description>"
user_invocable: true
---

# Test-Driven Development

Implement a feature using TDD methodology for the Lumineer project.

## Feature

$ARGUMENTS

## TDD Cycle

### Phase 1: RED — Write Failing Tests

1. Identify the test file location:
   - Python: `ai/tests/unit/` or `ai/tests/integration/`
   - Frontend: `frontend/src/**/*.test.ts`
   - Backend: `backend/src/**/*.test.ts`

2. Write test cases covering:
   - Happy path (expected behavior)
   - Edge cases (empty input, boundary values)
   - Error cases (invalid input, external failures)

3. Run the test — it MUST fail:
   ```bash
   # Python
   cd ai && pytest tests/unit/path/to/test.py -v

   # TypeScript
   cd frontend && bun test path/to/test.ts
   cd backend && bun test path/to/test.ts
   ```

### Phase 2: GREEN — Minimal Implementation

1. Write the minimum code to make tests pass
2. Follow Lumineer patterns:
   - Factory pattern for entities
   - Port/Adapter for external dependencies
   - Strategy pattern for Reranker/Formatter
3. Run tests — they MUST pass
4. Do NOT add features beyond what tests require

### Phase 3: REFACTOR — Improve

1. Clean up code while keeping tests green
2. Extract common patterns
3. Ensure naming is clear and consistent
4. Run tests after each refactor step

## Testing Rules

- Mock external dependencies via Port interfaces (not concrete implementations)
- Python: use `pytest` with `@pytest.mark.unit` / `@pytest.mark.integration`
- TypeScript: use `vitest` with `vi.mock()` for mocking
- Never test implementation details — test behavior

## Verification

After completing the cycle:
```bash
# Run full test suite for affected layer
cd ai && pytest
cd frontend && bun test
cd backend && bun test
```
