#!/bin/bash
# Block direct file edits to the main repo (develop branch)
# All changes must go through a worktree feature branch

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

MAIN_REPO="/Users/nakamurar39/develop/learning/courses/capstone/lumineer"
WORKTREE_BASE="/Users/nakamurar39/develop/learning/courses/capstone/worktree"

if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Block edits inside main repo but NOT inside worktrees
if [[ "$FILE_PATH" == "$MAIN_REPO/"* ]] && [[ "$FILE_PATH" != "$WORKTREE_BASE/"* ]]; then
  echo "⛔ BLOCKED: Direct edit to main repo detected."
  echo "   Path: $FILE_PATH"
  echo "   Use a worktree instead: $WORKTREE_BASE/<branch>/"
  exit 2
fi
