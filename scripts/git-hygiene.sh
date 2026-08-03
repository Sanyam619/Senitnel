#!/usr/bin/env bash
# Git hygiene checks for environment/repo in a Sentinel task.
set -euo pipefail

TASK_DIR="${1:?Usage: git-hygiene.sh <task-dir>}"
REPO="$TASK_DIR/environment/repo"
TOML="$TASK_DIR/task.toml"

if [[ ! -d "$REPO/.git" ]]; then
  echo "FAIL  $REPO/.git missing"
  exit 1
fi

cd "$REPO"
FAIL=0

check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "PASS  $label"
  else
    echo "FAIL  $label"
    FAIL=1
  fi
}

check "HEAD resolves" git rev-parse --verify HEAD

BASE=""
if [[ -f "$TOML" ]]; then
  BASE="$(grep -E 'base_commit_sha\s*=' "$TOML" 2>/dev/null | head -1 | sed -E 's/.*"([^"]+)".*/\1/' || true)"
fi

HEAD="$(git rev-parse HEAD 2>/dev/null || echo "")"
if [[ -n "$BASE" && -n "$HEAD" ]]; then
  if [[ "$BASE" == "$HEAD" ]]; then
    echo "PASS  HEAD matches base_commit_sha ($HEAD)"
  else
    echo "FAIL  HEAD ($HEAD) != base_commit_sha ($BASE) — realign task.toml to HEAD"
    FAIL=1
  fi
else
  echo "WARN  base_commit_sha not found in task.toml — verify HEAD manually"
fi

# Only sees commits parked on another ref (stray branch or tag). A commit made on
# HEAD's own branch moves HEAD, so the base_commit_sha comparison above is what
# catches that — which is why a missing base_commit_sha is worth fixing.
if [[ -z "$(git rev-list --all --not HEAD 2>/dev/null || true)" ]]; then
  echo "PASS  no commits beyond HEAD"
else
  echo "FAIL  leaked commits/branches/tags beyond HEAD"
  git rev-list --all --not HEAD 2>/dev/null | head -5 || true
  FAIL=1
fi

if [[ -z "$(git remote 2>/dev/null || true)" ]]; then
  echo "PASS  no remotes"
else
  echo "FAIL  remotes configured:"
  git remote -v
  FAIL=1
fi

if [[ -z "$(git config --local --get-regexp '^filter\.' 2>/dev/null || true)" ]]; then
  echo "PASS  no filter.* drivers"
else
  echo "FAIL  filter.* drivers present"
  FAIL=1
fi

if [[ -z "$(git status --porcelain 2>/dev/null || true)" ]]; then
  echo "PASS  clean working tree"
else
  echo "FAIL  dirty working tree"
  git status --porcelain
  FAIL=1
fi

if [[ ! -d .git/logs ]]; then
  echo "PASS  no reflog (.git/logs absent)"
else
  echo "FAIL  reflog present — expire and remove .git/logs"
  FAIL=1
fi

SIZE_KB="$(du -sk .git 2>/dev/null | awk '{print $1}')"
if [[ "$SIZE_KB" -lt 102400 ]]; then
  echo "PASS  .git size ${SIZE_KB}KB (< 100MB)"
else
  echo "FAIL  .git too large (${SIZE_KB}KB)"
  FAIL=1
fi

PATCH="$TASK_DIR/tests/tests.patch"
if [[ -f "$PATCH" ]]; then
  if git apply --check "$PATCH" 2>/dev/null; then
    echo "PASS  tests.patch applies cleanly"
  else
    echo "FAIL  tests.patch does not apply — regenerate against base commit"
    FAIL=1
  fi
else
  echo "WARN  tests/tests.patch missing"
fi

exit "$FAIL"
