---
description: General coding style rules (immutability, file organization, error handling)
---

# Coding Style

## Immutability

ALWAYS create new objects, NEVER mutate existing ones:

```typescript
// WRONG: mutation
function updateUser(user: User, name: string): User {
  user.name = name
  return user
}

// CORRECT: immutable update
function updateUser(user: Readonly<User>, name: string): User {
  return { ...user, name }
}
```

```python
# WRONG: mutation
user["name"] = new_name

# CORRECT: immutable
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    name: str
    email: str
```

## File Organization

MANY SMALL FILES > FEW LARGE FILES:
- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Extract utilities from large modules
- Organize by feature/domain, not by type

## Error Handling

- Handle errors explicitly at every level
- Provide user-friendly error messages in UI-facing code
- Log detailed error context on the server side
- Never silently swallow errors

```typescript
// CORRECT: narrow unknown errors safely
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  return "Unexpected error"
}
```

## Input Validation

- Validate all user input at system boundaries
- Use Zod (TypeScript) or Pydantic (Python) for schema-based validation
- Fail fast with clear error messages
- Never trust external data (API responses, user input, file content)

## TypeScript Specifics

- Use `interface` for object shapes, `type` for unions/intersections
- Prefer string literal unions over `enum`
- Avoid `any` — use `unknown` for untrusted input, then narrow safely
- No `console.log` in production code — use proper logging
- Explicit types on exported functions; let TS infer local variables

## Python Specifics

- Follow PEP 8 conventions
- Use type annotations on all function signatures
- Prefer `@dataclass(frozen=True)` and `NamedTuple` for immutable data
- Use `ruff` for linting + formatting
- Use `Protocol` for duck typing (matches Port/Adapter pattern)

## Code Quality Checklist

Before marking work complete:
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values (use constants or config)
- [ ] Immutable patterns used
