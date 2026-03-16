#!/bin/bash
# Warn about console.log/print() statements after edits
# Does not block (exit 0), just warns

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') or d.get('tool_result',{}).get('file_path',''))" 2>/dev/null)

if [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# Skip test files
if [[ "$FILE_PATH" == *"/test/"* ]] || [[ "$FILE_PATH" == *"/tests/"* ]] || [[ "$FILE_PATH" == *".test."* ]] || [[ "$FILE_PATH" == *"_test."* ]]; then
  exit 0
fi

case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx)
    MATCHES=$(grep -n "console\.log" "$FILE_PATH" 2>/dev/null)
    if [[ -n "$MATCHES" ]]; then
      echo "⚠️  console.log found in $(basename "$FILE_PATH"):"
      echo "$MATCHES" | head -5
      echo "   Consider using a proper logger instead."
    fi
    ;;
  *.py)
    MATCHES=$(grep -n "^\s*print(" "$FILE_PATH" 2>/dev/null)
    if [[ -n "$MATCHES" ]]; then
      echo "⚠️  print() found in $(basename "$FILE_PATH"):"
      echo "$MATCHES" | head -5
      echo "   Consider using the logging module instead."
    fi
    ;;
esac

exit 0
