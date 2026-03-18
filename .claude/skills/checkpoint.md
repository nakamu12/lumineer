---
description: "Create a checkpoint commit to save current progress. Usage: /checkpoint [message]"
user_invocable: true
---

# Checkpoint

Create a checkpoint commit to save current work-in-progress.

## Process

1. **Check Status**
   ```bash
   git status
   git diff --stat
   ```

2. **Run Quick Checks** (fail = warn, don't block)
   - Check for secrets in staged files
   - Check for `console.log` in TypeScript files
   - Check for `print()` in Python files (except tests)

3. **Create Checkpoint Commit**
   - Stage all changes: `git add -A`
   - Commit with message:
     - If $ARGUMENTS provided: `wip: $ARGUMENTS`
     - If no arguments: auto-generate from changed files

4. **Output Summary**
   - Files changed count
   - Lines added/removed
   - Commit hash
   - Reminder: "This is a WIP commit — squash before PR"

## Rules

- Checkpoint commits use `wip:` prefix
- These MUST be squashed or amended before creating a PR
- Do not push checkpoint commits to remote
