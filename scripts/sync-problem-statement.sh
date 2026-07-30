#!/usr/bin/env bash
# Copy instruction.md → environment/problem_statement.md (must be identical).
set -euo pipefail

TASK_DIR="${1:?Usage: sync-problem-statement.sh <task-dir>}"
INST="$TASK_DIR/instruction.md"
PROB="$TASK_DIR/environment/problem_statement.md"

if [[ ! -f "$INST" ]]; then
  echo "ERROR: missing $INST" >&2
  exit 1
fi

mkdir -p "$(dirname "$PROB")"
cp "$INST" "$PROB"
echo "Synced $PROB from instruction.md"
