#!/usr/bin/env bash
# Full Sentinel pre-upload gate.
#
# Runs everything that can be checked locally, in the order the platform checks it:
#   structure/metadata -> git hygiene -> docker build -> oracle 1.0 / NOP 0.0
# Optionally runs the Harbor rubric judge, the closest local stand-in for the
# blocking Quality Check.
#
# Usage: preflight.sh <task-dir> [--fast] [--no-docker] [--no-oracle] [--rubric]
#
#   --fast       structure + git only (quick iteration; not an upload gate)
#   --no-docker  skip the local image build
#   --no-oracle  skip the oracle/NOP trials
#   --rubric     also run `harbor check` (needs model credentials)
#
# --docker / --harbor are accepted for backwards compatibility and are now the default.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TASK_DIR="${1:?Usage: preflight.sh <task-dir> [--fast] [--no-docker] [--no-oracle] [--rubric]}"
shift || true

DO_DOCKER=1
DO_ORACLE=1
DO_RUBRIC=0
PRINT_IMAGE=0

for arg in "$@"; do
  case "$arg" in
    --fast)      DO_DOCKER=0; DO_ORACLE=0 ;;
    --no-docker) DO_DOCKER=0 ;;
    --no-oracle) DO_ORACLE=0 ;;
    --rubric)    DO_RUBRIC=1 ;;
    --print-image) PRINT_IMAGE=1 ;;
    --docker|--harbor) ;;  # now the default
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

TASK_DIR="$(cd "$TASK_DIR" && pwd)"
NAME="$(basename "$TASK_DIR")"
# Docker tags must be lowercase and start and end alphanumeric. A truncated task
# id ends on a hyphen often enough that building it raw reports a bogus build
# failure against the task.
SLUG="$(
  printf '%s' "$NAME" \
    | tr '[:upper:]' '[:lower:]' \
    | tr -cs 'a-z0-9' '-' \
    | cut -c1-40 \
    | sed -E 's/^-+//; s/-+$//'
)"
IMAGE="sentinel-preflight-${SLUG:-task}"

if [[ "$PRINT_IMAGE" -eq 1 ]]; then
  echo "$IMAGE"
  exit 0
fi
# Never write scratch output inside the task directory — it would ship in the zip
# and hard-cap the packaging axis.
WORK_DIR="$ROOT/.preflight/$NAME"
mkdir -p "$WORK_DIR"
FAIL=0
WARNED=0

section() { printf '\n=== %s ===\n' "$1"; }
fail()    { echo "FAIL  $1"; FAIL=1; }
warn()    { echo "WARN  $1"; WARNED=1; }

# A validator whose checks have silently stopped firing is worse than none, so
# prove it still catches every defect class before trusting its verdict.
# SENTINEL_SELFTEST=1 breaks the cycle when selftest.py is the one calling us.
section "Toolchain self-test"
if [[ "${SENTINEL_SELFTEST:-}" == "1" ]]; then
  echo "SKIP  invoked from scripts/selftest.py"
else
  if python3 "$ROOT/scripts/selftest.py" > "$WORK_DIR/selftest.log" 2>&1; then
    echo "PASS  $(tail -1 "$WORK_DIR/selftest.log" | sed 's/^PASS  *//')"
  else
    fail "scripts/selftest.py — the validator itself is broken, see $WORK_DIR/selftest.log"
    tail -15 "$WORK_DIR/selftest.log" | sed 's/^/      /'
  fi
  if ! python3 "$ROOT/scripts/check-docs.py"; then
    fail "scripts/check-docs.py — the docs contradict the tooling, so one of them is lying"
  fi
fi

section "Structure & metadata"
if ! python3 "$ROOT/scripts/validate_task.py" "$TASK_DIR"; then
  FAIL=1
fi

section "Git hygiene"
if ! "$ROOT/scripts/git-hygiene.sh" "$TASK_DIR"; then
  FAIL=1
fi

section "Solution artifacts"
if [[ -f "$TASK_DIR/solution/solution.patch" && ! -f "$TASK_DIR/solution/golden.patch" ]]; then
  fail "rename solution/solution.patch to solution/golden.patch"
fi
if [[ ! -x "$TASK_DIR/solution/solve.sh" ]]; then
  warn "solution/solve.sh is not executable — chmod +x before zipping"
fi
if [[ ! -x "$TASK_DIR/tests/test.sh" ]]; then
  warn "tests/test.sh is not executable — chmod +x before zipping"
fi

if [[ "$DO_DOCKER" -eq 1 ]]; then
  section "Docker build"
  if ! command -v docker >/dev/null 2>&1; then
    fail "docker not found — the environment build is a required pre-upload check"
  elif ! docker info >/dev/null 2>&1; then
    fail "docker is installed but the daemon is not running — start Docker Desktop"
  elif docker build -t "$IMAGE" "$TASK_DIR/environment" > "$WORK_DIR/docker-build.log" 2>&1; then
    echo "PASS  docker build ($IMAGE)"
  else
    fail "docker build — the platform build will fail the same way"
    tail -25 "$WORK_DIR/docker-build.log" | sed 's/^/      /'
    echo "      full log: $WORK_DIR/docker-build.log"
  fi
fi

# --------------------------------------------------------------------------- #
# Oracle must reach reward 1.0; NOP must reach 0.0. These are the checks that
# send a task back to NEEDS_REVISION most often, so they run by default.
# --------------------------------------------------------------------------- #
run_trial() {
  local agent="$1" expected="$2"
  local jobs_dir="$WORK_DIR/$agent"
  rm -rf "$jobs_dir"
  mkdir -p "$jobs_dir"

  echo "--- harbor run -a $agent (expect reward $expected)"
  if ! harbor run -p "$TASK_DIR" -a "$agent" -o "$jobs_dir" >"$jobs_dir/harbor.log" 2>&1; then
    echo "      harbor exited non-zero; tail of log:"
    tail -15 "$jobs_dir/harbor.log" | sed 's/^/      /'
  fi

  local reward_file
  reward_file="$(find "$jobs_dir" -name reward.txt -print -quit 2>/dev/null)"
  if [[ -z "$reward_file" ]]; then
    fail "$agent trial produced no reward.txt — see $jobs_dir/harbor.log"
    return
  fi

  local reward
  reward="$(tr -d '[:space:]' < "$reward_file")"
  if awk -v r="$reward" -v e="$expected" 'BEGIN { exit !(r+0 == e+0) }'; then
    echo "PASS  $agent reward = $reward"
  else
    fail "$agent reward = $reward (expected $expected) — see $reward_file"
  fi
}

if [[ "$DO_ORACLE" -eq 1 ]]; then
  section "Oracle / NOP"
  if command -v harbor >/dev/null 2>&1; then
    run_trial oracle 1.0
    run_trial nop 0.0
  else
    warn "harbor CLI not found — oracle/NOP could not run locally."
    warn "Valid-as-is REQUIRES a local oracle+NOP run (the platform does not re-run them)."
  fi
fi

if [[ "$DO_RUBRIC" -eq 1 ]]; then
  section "Rubric judge (local stand-in for Quality Check)"
  if ! command -v harbor >/dev/null 2>&1; then
    warn "harbor CLI not found — cannot run the rubric judge"
  elif [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    # harbor check calls Anthropic directly; without the key it exits 1 after ~20s.
    warn "ANTHROPIC_API_KEY is not set, so the rubric judge cannot run. To enable it:"
    warn "  export ANTHROPIC_API_KEY=sk-ant-...   then re-run with --rubric"
  elif harbor check "$TASK_DIR" -o "$WORK_DIR/rubric.json" 2>&1 | tee "$WORK_DIR/rubric.log"; then
    echo "Report: $WORK_DIR/rubric.json"
    echo "Read the per-axis scores; test_coverage and test_faithfulness are blocking."
  else
    warn "harbor check did not complete — see $WORK_DIR/rubric.log"
  fi
fi

section "Summary"
if [[ "$DO_DOCKER" -eq 0 || "$DO_ORACLE" -eq 0 ]]; then
  warn "partial run — a full gate needs the docker build and the oracle/NOP trials"
fi

if [[ "$FAIL" -eq 0 ]]; then
  if [[ "$WARNED" -eq 1 ]]; then
    echo "PASS with warnings — read every WARN above before you upload."
    echo "Warnings are the things reviewers flag; treat them as work, not noise."
  else
    echo "PASS  clean — ready to zip"
  fi
  echo "Next: $ROOT/scripts/zip-task.sh $TASK_DIR"
  exit 0
fi

echo "FAIL  fix the failures above before uploading."
echo "Uploading a task with known failures burns a revision cycle."
exit 1
