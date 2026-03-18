---
description: "Create an implementation plan for a feature or task. Usage: /plan <description>"
user_invocable: true
---

# Implementation Planning

You are a planning agent for the Lumineer project (3-layer architecture: React frontend + Hono/TypeScript backend + Python AI processing).

## Input

The user has requested a plan for: $ARGUMENTS

## Process

1. **Understand the Request**
   - Parse what the user wants to achieve
   - Identify which layers are affected (frontend / backend / ai / gateway / infra)

2. **Research the Codebase**
   - Read relevant existing code to understand current state
   - Check CLAUDE.md, docs/requirements.md, docs/adr.md for constraints
   - Identify dependencies and integration points between layers

3. **Create the Plan**
   - Break down into phases (each phase = one PR-able unit)
   - For each phase, list:
     - Files to create/modify
     - Key design decisions
     - Dependencies on other phases
   - Identify risks and open questions

4. **Output Format**

```markdown
## Plan: <title>

### Affected Layers
- [ ] Frontend (React + Shadcn UI)
- [ ] Backend (Hono + TypeScript)
- [ ] AI Processing (Python + Litestar)
- [ ] Gateway (Hono proxy)
- [ ] Infrastructure (Docker, CI/CD)

### Phase 1: <name>
**Branch**: LM{NNNN}-{type}/{scope}-{detail}
**Files**:
- `path/to/file.ts` — description of changes
**Design Decisions**:
- Decision and rationale
**Risks**:
- Risk and mitigation

### Phase 2: <name>
...

### Open Questions
- Question that needs user input
```

5. **Validate Against Rules**
   - Clean Architecture: dependency direction correct?
   - Factory pattern for entities?
   - Port/Adapter for external dependencies?
   - Prompts externalized to `prompts/*.md`?
   - No direct Frontend → AI Processing calls?
