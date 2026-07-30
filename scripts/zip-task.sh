#!/usr/bin/env bash
# Zip flat task contents for Snorkel upload (preserves empty .git dirs).
set -euo pipefail

TASK_DIR="${1:?Usage: zip-task.sh <task-dir> [output.zip]}"
OUT="${2:-}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TASK_DIR="$(cd "$TASK_DIR" && pwd)"

if [[ ! -f "$TASK_DIR/instruction.md" ]]; then
  echo "ERROR: $TASK_DIR does not look like a task root (no instruction.md)" >&2
  exit 1
fi

if [[ -z "$OUT" ]]; then
  NAME="$(basename "$TASK_DIR")"
  OUT="$ROOT/tasks/out/${NAME}.zip"
fi

mkdir -p "$(dirname "$OUT")"

# Preflight reminder
if ! "$ROOT/scripts/validate_task.py" "$TASK_DIR" >/dev/null 2>&1; then
  echo "WARN: validate_task.py failed — fix before uploading" >&2
  "$ROOT/scripts/validate_task.py" "$TASK_DIR" || true
fi

(
  cd "$TASK_DIR"
  zip -rX "$OUT" . -x '*.DS_Store' '__MACOSX/*'
)

echo "Created $OUT"
echo "Verify git dirs preserved:"
unzip -l "$OUT" | grep 'refs/' | head -5 || echo "  (no refs/ entries — check .git was included)"
