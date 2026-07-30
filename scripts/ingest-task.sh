#!/usr/bin/env bash
# Ingest a zip from tasks/inbox/ → unpack to tasks/active/<name>/.
# Usage: ingest-task.sh my-task.zip
#    or: ingest-task.sh tasks/inbox/my-task.zip
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT="${1:?Usage: ingest-task.sh <zip-filename-or-path>}"

if [[ -f "$INPUT" ]]; then
  ZIP="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"
elif [[ -f "$ROOT/tasks/inbox/$INPUT" ]]; then
  ZIP="$ROOT/tasks/inbox/$INPUT"
elif [[ -f "$ROOT/tasks/inbox/${INPUT%.zip}.zip" ]]; then
  ZIP="$ROOT/tasks/inbox/${INPUT%.zip}.zip"
else
  echo "ERROR: zip not found: $INPUT" >&2
  echo "       looked in: $ROOT/tasks/inbox/" >&2
  exit 1
fi

NAME="$(basename "$ZIP" .zip)"
DEST="$ROOT/tasks/active/$NAME"

echo "Ingesting: $ZIP"
echo "       → $DEST"
"$ROOT/scripts/unpack-task.sh" "$ZIP" "tasks/active/$NAME"

echo ""
echo "Active task:  tasks/active/$NAME"
echo "Runs (ref):   tasks/active/${NAME}_runs  (if present)"
echo "Upload zip:   tasks/out/${NAME}.zip  (after preflight)"
