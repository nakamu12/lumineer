---
description: "Diagnose and fix build/lint/typecheck errors across all layers. Usage: /build-fix [layer]"
user_invocable: true
---

# Build Fix

Diagnose and fix build, lint, or typecheck errors in the Lumineer project.

## Target Layer

If $ARGUMENTS specifies a layer (frontend, backend, gateway, ai), focus on that layer.
Otherwise, run checks on all layers.

## Process

### Step 1: Run Checks

Run the following checks in parallel where possible:

**Frontend** (if applicable):
```bash
cd frontend && bun run lint && bun run typecheck
```

**Backend** (if applicable):
```bash
cd backend && bun run lint && bun run typecheck
```

**Gateway** (if applicable):
```bash
cd gateway && bun run lint && bun run typecheck
```

**AI Processing** (if applicable):
```bash
cd ai && ruff check . && ruff format --check . && mypy .
```

### Step 2: Analyze Errors

- Read the full error output
- Categorize errors: type errors, lint violations, import issues, syntax errors
- Identify root causes (one fix may resolve multiple errors)

### Step 3: Fix Incrementally

1. Fix one error category at a time
2. Start with the root cause (often import/type errors cascade)
3. Re-run checks after each fix to verify
4. Do NOT suppress errors with `// @ts-ignore` or `# type: ignore` unless absolutely necessary

### Step 4: Verify

Re-run all checks to confirm zero errors before reporting success.

## Common Fixes

| Error | Fix |
|-------|-----|
| Missing import | Add the import statement |
| Type mismatch | Fix the type, not the check |
| Unused variable | Remove it (don't prefix with `_` unless intentional) |
| ruff format | Run `ruff format .` to auto-fix |
| Prettier | Run `bun run format` to auto-fix |
