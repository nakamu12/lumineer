#!/bin/bash
# Auto-format files after Edit/Write operations
# Runs Prettier for TS/TSX/JS files and ruff for Python files

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') or d.get('tool_result',{}).get('file_path',''))" 2>/dev/null)

if [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# Get the project root from the file path
PROJECT_ROOT=""
if [[ "$FILE_PATH" == *"/frontend/"* ]]; then
  PROJECT_ROOT="${FILE_PATH%%/frontend/*}/frontend"
elif [[ "$FILE_PATH" == *"/backend/"* ]]; then
  PROJECT_ROOT="${FILE_PATH%%/backend/*}/backend"
elif [[ "$FILE_PATH" == *"/gateway/"* ]]; then
  PROJECT_ROOT="${FILE_PATH%%/gateway/*}/gateway"
elif [[ "$FILE_PATH" == *"/ai/"* ]]; then
  PROJECT_ROOT="${FILE_PATH%%/ai/*}/ai"
fi

case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx)
    if [[ -n "$PROJECT_ROOT" ]] && [[ -f "$PROJECT_ROOT/.prettierrc" ]]; then
      cd "$PROJECT_ROOT" && bunx prettier --write "$FILE_PATH" 2>/dev/null
    fi
    ;;
  *.py)
    if command -v ruff &>/dev/null; then
      ruff format "$FILE_PATH" 2>/dev/null
    fi
    ;;
esac

exit 0
