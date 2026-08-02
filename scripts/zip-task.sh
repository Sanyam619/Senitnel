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

# Block upload zips that bundle node_modules (Dockerfile runs npm ci at build time).
# Preflight/docker tests often recreate node_modules under environment/repo/.
NODE_MODULES=(
  "$TASK_DIR/environment/repo/node_modules"
  "$TASK_DIR/environment/repo/frontend/node_modules"
)
for nm in "${NODE_MODULES[@]}"; do
  if [[ -d "$nm" ]]; then
    echo "ERROR: $nm must not ship in the upload zip (run: rm -rf \"$nm\")" >&2
    echo "       node_modules is installed at Docker build time; bundling it causes" >&2
    echo "       oversized zips and Snorkel S3/GuardDuty availability timeouts." >&2
    exit 1
  fi
done

REPO="$TASK_DIR/environment/repo"
if [[ -d "$REPO/.git" ]]; then
  if [[ -n "$(git -C "$REPO" status --porcelain 2>/dev/null || true)" ]]; then
    echo "ERROR: environment/repo has a dirty working tree — reset before zipping:" >&2
    echo "       cd \"$REPO\" && git reset --hard HEAD && git clean -fd" >&2
    exit 1
  fi
  # CDG static check fails on .git/logs — strip reflog (git metadata hygiene only).
  if [[ -d "$REPO/.git/logs" ]]; then
    echo "Stripping git reflog (.git/logs) before zip..."
    git -C "$REPO" reflog expire --expire=now --all 2>/dev/null || true
    git -C "$REPO" gc --prune=now 2>/dev/null || true
    rm -rf "$REPO/.git/logs"
  fi
fi

# Hard gate — git hygiene + validate (CDG static checks mirror git-hygiene.sh).
if ! "$ROOT/scripts/git-hygiene.sh" "$TASK_DIR"; then
  echo "ERROR: git-hygiene.sh failed — fix before zipping" >&2
  exit 1
fi

(
  cd "$TASK_DIR"
  rm -f "$OUT"
  zip -rX "$OUT" . \
    -x '*.DS_Store' \
    -x '__MACOSX/*' \
    -x '*/node_modules/*' \
    -x '*/node_modules/**'
)

ZIP_BYTES="$(wc -c < "$OUT" | tr -d ' ')"
MAX_ZIP_BYTES=$((80 * 1024 * 1024))  # 80 MiB — Sentinel tasks should be source + .git only
if [[ "$ZIP_BYTES" -gt "$MAX_ZIP_BYTES" ]]; then
  ZIP_MB=$((ZIP_BYTES / 1024 / 1024))
  echo "ERROR: zip is too large (${ZIP_MB} MiB, max 80 MiB)." >&2
  echo "       Likely stray node_modules or build artifacts under environment/repo/." >&2
  rm -f "$OUT"
  exit 1
fi

ZIP_MB=$((ZIP_BYTES / 1024 / 1024))
echo "Created $OUT (${ZIP_MB} MiB)"
echo "Verify git dirs preserved:"
unzip -l "$OUT" | grep 'refs/' | head -5 || echo "  (no refs/ entries — check .git was included)"
