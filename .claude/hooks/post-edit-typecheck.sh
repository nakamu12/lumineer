#!/bin/bash
# Run TypeScript type check after editing .ts/.tsx files
# Reports warnings but does not block (exit 0)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') or d.get('tool_result',{}).get('file_path',''))" 2>/dev/null)

if [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# Only check TypeScript files
case "$FILE_PATH" in
  *.ts|*.tsx) ;;
  *) exit 0 ;;
esac

# Determine project root
PROJECT_ROOT=""
if [[ "$FILE_PATH" == *"/frontend/"* ]]; then
  PROJECT_ROOT="${FILE_PATH%%/frontend/*}/frontend"
elif [[ "$FILE_PATH" == *"/backend/"* ]]; then
  PROJECT_ROOT="${FILE_PATH%%/backend/*}/backend"
elif [[ "$FILE_PATH" == *"/gateway/"* ]]; then
  PROJECT_ROOT="${FILE_PATH%%/gateway/*}/gateway"
fi

if [[ -n "$PROJECT_ROOT" ]] && [[ -f "$PROJECT_ROOT/tsconfig.json" ]]; then
  ERRORS=$(cd "$PROJECT_ROOT" && bunx tsc --noEmit 2>&1 | head -20)
  if [[ -n "$ERRORS" ]] && [[ "$ERRORS" != *"error TS"* ]]; then
    exit 0
  fi
  if [[ "$ERRORS" == *"error TS"* ]]; then
    echo "⚠️  TypeScript errors detected in $(basename "$PROJECT_ROOT"):"
    echo "$ERRORS"
  fi
fi

# Always exit 0 — warn only, don't block
exit 0
