#!/usr/bin/env bash
set -euo pipefail
CASE=""
ROOT="/data/fixtures"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --case) CASE="$2"; shift 2 ;;
    --root) ROOT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
if [[ -z "$CASE" ]]; then
  echo "usage: run-case.sh --case <name> [--root /data/fixtures]" >&2
  exit 2
fi
/opt/csp/bin/cspd "$CASE" "$ROOT"
