---
description: Performance optimization and context window management rules
---

# Performance

## Model Selection for Subagents

| Model | Use Case |
|-------|----------|
| **haiku** | Lightweight agents, frequent invocation, worker agents |
| **sonnet** | Main development, orchestrating multi-agent workflows |
| **opus** | Complex architectural decisions, deep reasoning, research |

## Context Window Management

Avoid last 20% of context window for:
- Large-scale refactoring
- Feature implementation spanning multiple files
- Debugging complex interactions

Lower context sensitivity (safe in late context):
- Single-file edits
- Independent utility creation
- Documentation updates
- Simple bug fixes

## Parallel Execution

ALWAYS use parallel task execution for independent operations:
- Launch multiple agents in parallel when tasks don't depend on each other
- Run independent searches, reads, and analyses concurrently
- Only serialize when there are data dependencies

## Build Troubleshooting

If build fails:
1. Read the full error output carefully
2. Fix the root cause (not symptoms)
3. Fix incrementally — one error at a time
4. Verify after each fix before moving to the next
