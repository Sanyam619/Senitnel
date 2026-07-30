#!/usr/bin/env bash
# Unpack a Snorkel download zip into tasks/active/<name>.
# Handles zips that contain task/ wrapper or flat task contents.
set -euo pipefail

ZIP="${1:?Usage: unpack-task.sh <zip> [dest-dir]}"
DEST="${2:-}"

if [[ -z "$DEST" ]]; then
  BASE="$(basename "$ZIP" .zip)"
  DEST="tasks/active/$BASE"
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/$DEST"
TMP="$(mktemp -d)"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

unzip -q "$ZIP" -d "$TMP"

# Detect layout: task/ subfolder vs flat
if [[ -d "$TMP/task" && -f "$TMP/task/instruction.md" ]]; then
  SRC="$TMP/task"
elif [[ -f "$TMP/instruction.md" ]]; then
  SRC="$TMP"
else
  echo "ERROR: cannot find instruction.md in zip" >&2
  find "$TMP" -maxdepth 3 -name 'instruction.md' 2>/dev/null || true
  exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "$SRC/." "$DEST/"

# Rename legacy solution.patch
if [[ -f "$DEST/solution/solution.patch" && ! -f "$DEST/solution/golden.patch" ]]; then
  mv "$DEST/solution/solution.patch" "$DEST/solution/golden.patch"
  echo "Renamed solution.patch → golden.patch"
fi

# Copy runs/ to sibling if present (reference only)
if [[ -d "$TMP/runs" ]]; then
  RUNS_DEST="${DEST}_runs"
  rm -rf "$RUNS_DEST"
  cp -a "$TMP/runs" "$RUNS_DEST"
  echo "Agent runs copied to ${RUNS_DEST} (reference only — do not upload)"
fi

echo "Unpacked to $DEST"
echo "Next: ./scripts/preflight.sh $DEST"
