---
description: "Review code changes for quality, security, and architecture compliance. Usage: /code-review [file or branch]"
user_invocable: true
---

# Code Review

Review the current changes for quality, security, and compliance with Lumineer's architecture rules.

## Target

If $ARGUMENTS is provided, review that specific file or branch diff.
Otherwise, review all uncommitted changes (`git diff` + `git diff --staged`).

## Review Checklist

### 1. Architecture Compliance
- [ ] Dependency direction: `interfaces/ → usecases/ → ports/ ← infrastructure/`
- [ ] No Frontend → AI Processing direct calls
- [ ] Factory pattern for entity creation (no `new Entity()`)
- [ ] Port/Adapter for external dependencies (LLM, VectorDB, Embedding)
- [ ] Prompts externalized to `prompts/*.md` (no hardcoded strings)

### 2. Code Quality
- [ ] Functions < 50 lines, files < 800 lines
- [ ] Immutable patterns (no mutation)
- [ ] Proper error handling (no swallowed errors)
- [ ] Input validation at system boundaries
- [ ] No `any` in TypeScript (use `unknown` + narrowing)
- [ ] Type annotations on all Python function signatures

### 3. Security
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] No PII sent to LLM without masking
- [ ] No Qdrant payload raw data exposed to frontend
- [ ] Environment variables via Pydantic Settings / process.env

### 4. Testing
- [ ] Unit tests added/updated for changed code
- [ ] External dependencies mocked via Port interface
- [ ] LLM-related changes: Golden Dataset evaluation needed?

### 5. Language Policy
- [ ] All code in English (variables, functions, classes, comments)
- [ ] All UI text in English

## Output Format

For each issue found:
```
**[CRITICAL/HIGH/MEDIUM/LOW]** file:line — description
  Suggestion: how to fix
```

Summarize with counts: X critical, Y high, Z medium, W low.
