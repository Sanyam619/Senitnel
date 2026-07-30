#!/usr/bin/env bash
# Full Sentinel pre-upload checklist.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TASK_DIR="${1:?Usage: preflight.sh <task-dir> [--docker] [--harbor]}"
DO_DOCKER=0
DO_HARBOR=0

shift || true
for arg in "$@"; do
  case "$arg" in
    --docker) DO_DOCKER=1 ;;
    --harbor) DO_HARBOR=1 ;;
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

TASK_DIR="$(cd "$TASK_DIR" && pwd)"
FAIL=0

section() { echo; echo "=== $1 ==="; }

section "Structure & metadata"
if python3 "$ROOT/scripts/validate_task.py" "$TASK_DIR" --strict; then
  :
else
  FAIL=1
fi

section "Git hygiene"
if "$ROOT/scripts/git-hygiene.sh" "$TASK_DIR"; then
  :
else
  FAIL=1
fi

section "Solution artifacts"
if [[ -f "$TASK_DIR/solution/solution.patch" && ! -f "$TASK_DIR/solution/golden.patch" ]]; then
  echo "FAIL  Rename solution/solution.patch → solution/golden.patch"
  FAIL=1
fi
if [[ -f "$TASK_DIR/solution/golden.patch" ]]; then
  LINES="$(wc -l < "$TASK_DIR/solution/golden.patch" | tr -d ' ')"
  echo "INFO  golden.patch: $LINES lines (expect substantive fix ~100+ lines across 2+ files)"
fi

if [[ "$DO_DOCKER" -eq 1 ]]; then
  section "Docker build"
  if docker build -t sentinel-preflight "$TASK_DIR/environment"; then
    echo "PASS  docker build"
  else
    echo "FAIL  docker build"
    FAIL=1
  fi
fi

if [[ "$DO_HARBOR" -eq 1 ]]; then
  section "Harbor oracle / NOP"
  if command -v harbor >/dev/null 2>&1; then
    harbor run -p "$TASK_DIR" -a oracle || { echo "FAIL  oracle"; FAIL=1; }
    harbor run -p "$TASK_DIR" -a nop || { echo "FAIL  nop (expected 0.0)"; FAIL=1; }
  else
    echo "WARN  harbor CLI not installed — skip or install for local oracle/NOP"
  fi
fi

section "Summary"
if [[ "$FAIL" -eq 0 ]]; then
  echo "PASS  Preflight complete — ready to zip and upload"
  echo "Run: ./scripts/zip-task.sh $TASK_DIR"
  exit 0
fi

echo "FAIL  Fix errors above before uploading"
exit 1
