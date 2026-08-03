#!/usr/bin/env bash
# Zip the flat task contents for Snorkel upload (preserving empty .git dirs).
#
# This is a gate, not a packer: it refuses to produce a zip that would fail the
# platform's static or packaging checks.
#
# Usage: zip-task.sh <task-dir> [output.zip]
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
  OUT="$ROOT/tasks/out/$(basename "$TASK_DIR").zip"
fi
# Must be absolute: the zip runs from inside the task dir, and a relative path
# would write the archive into the task itself.
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"

# --------------------------------------------------------------------------- #
# 1. runs/ must never ship.
# --------------------------------------------------------------------------- #
if [[ -d "$TASK_DIR/runs" ]]; then
  echo "ERROR: runs/ is inside the task directory — move it out before zipping." >&2
  exit 1
fi

# --------------------------------------------------------------------------- #
# 2. Stray artifacts: a single one hard-caps the packaging axis at 1.
#    node_modules also blows up the zip (installed at docker build time).
# --------------------------------------------------------------------------- #
STRAY="$(find "$TASK_DIR" \
  \( -name '__pycache__' -o -name '*.pyc' -o -name '.DS_Store' \
     -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \
     -o -name '.venv' -o -name 'node_modules' -o -name '.idea' -o -name '.vscode' \
     -o -name '*.swp' -o -name '*.orig' -o -name '*.bak' -o -name '__MACOSX' \) \
  -not -path '*/.git/*' -print 2>/dev/null | head -20 || true)"

if [[ -n "$STRAY" ]]; then
  echo "ERROR: stray artifacts would ship in the zip (packaging axis caps at 1):" >&2
  echo "$STRAY" | sed 's/^/       /' >&2
  echo "       Delete them and re-run. node_modules is installed at docker build time." >&2
  exit 1
fi

# --------------------------------------------------------------------------- #
# 3. Git metadata hygiene (tracked source is never touched).
# --------------------------------------------------------------------------- #
REPO="$TASK_DIR/environment/repo"
if [[ -d "$REPO/.git" ]]; then
  if [[ -n "$(git -C "$REPO" status --porcelain 2>/dev/null || true)" ]]; then
    echo "ERROR: environment/repo has a dirty working tree — reset before zipping:" >&2
    echo "       cd \"$REPO\" && git reset --hard HEAD && git clean -fd" >&2
    exit 1
  fi
  # The platform's static check fails on a reflog.
  if [[ -d "$REPO/.git/logs" ]]; then
    echo "Stripping git reflog (.git/logs) before zip..."
    git -C "$REPO" reflog expire --expire=now --all 2>/dev/null || true
    git -C "$REPO" gc --prune=now 2>/dev/null || true
    rm -rf "$REPO/.git/logs"
  fi
fi

# --------------------------------------------------------------------------- #
# 4. Hard gates: structure/metadata/tests, then git checks.
#    The validator is tested first — this gate is only as good as the checks
#    behind it, and a check that has stopped firing looks identical to a pass.
# --------------------------------------------------------------------------- #
# SENTINEL_SELFTEST=1 is set when selftest.py is the caller, which would otherwise recurse.
if [[ "${SENTINEL_SELFTEST:-}" != "1" ]]; then
  echo "Running validator self-test..."
  if ! python3 "$ROOT/scripts/selftest.py" >/dev/null 2>&1; then
    echo "ERROR: scripts/selftest.py failed — validate_task.py is broken, so its verdict on" >&2
    echo "       this task means nothing. Run it directly for the details." >&2
    exit 1
  fi
fi

echo "Running validate_task.py gate..."
if ! python3 "$ROOT/scripts/validate_task.py" "$TASK_DIR"; then
  echo "ERROR: validate_task.py failed — fix the failures before zipping." >&2
  exit 1
fi

echo "Running git-hygiene.sh gate..."
if ! "$ROOT/scripts/git-hygiene.sh" "$TASK_DIR"; then
  echo "ERROR: git-hygiene.sh failed — fix before zipping." >&2
  exit 1
fi

# --------------------------------------------------------------------------- #
# 5. Zip flat contents. -X strips macOS attrs; no -D so empty .git/refs/
#    directory entries survive (dropping them breaks the repo on the platform).
# --------------------------------------------------------------------------- #
(
  cd "$TASK_DIR"
  rm -f "$OUT"
  zip -rX "$OUT" . \
    -x '*.DS_Store' \
    -x '__MACOSX/*' \
    -x '*/node_modules/*' \
    -x '*/__pycache__/*' >/dev/null
)

ZIP_BYTES="$(wc -c < "$OUT" | tr -d ' ')"
ZIP_MB=$((ZIP_BYTES / 1024 / 1024))
MAX_ZIP_BYTES=$((80 * 1024 * 1024))  # local guard: 255MB upload tripped an S3/GuardDuty timeout

if [[ "$ZIP_BYTES" -gt "$MAX_ZIP_BYTES" ]]; then
  echo "ERROR: zip is ${ZIP_MB} MiB (local limit 80 MiB)." >&2
  echo "       Usually stray build output or a bloated .git under environment/repo/." >&2
  echo "       Try: git -C \"$REPO\" gc --aggressive --prune=now" >&2
  rm -f "$OUT"
  exit 1
fi

# --------------------------------------------------------------------------- #
# 6. Post-zip verification: the archive must unpack flat and keep git dirs.
# --------------------------------------------------------------------------- #
LISTING="$(unzip -l "$OUT")"   # captured once: `unzip | grep -q` trips pipefail via SIGPIPE

if ! grep -q ' instruction.md$' <<<"$LISTING"; then
  echo "ERROR: instruction.md is not at the zip root — the archive is not flat." >&2
  exit 1
fi
if grep -qE '   (task|runs)/' <<<"$LISTING"; then
  echo "ERROR: zip contains a task/ or runs/ directory — upload must be flat contents." >&2
  exit 1
fi
if ! grep -q 'refs/' <<<"$LISTING"; then
  echo "ERROR: no .git refs/ entries in the archive — git will fail on the platform." >&2
  exit 1
fi

echo
echo "Created $OUT (${ZIP_MB} MiB)"
echo "Flat layout, git refs preserved, no stray artifacts."
if [[ "$ZIP_MB" -gt 40 ]]; then
  echo "NOTE  ${ZIP_MB} MiB is large; if the upload stalls, shrink .git and re-zip."
fi
