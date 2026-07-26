#!/usr/bin/env bash
set -euo pipefail
DAY=""
ROOT="/data/fixtures"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --day) DAY="$2"; shift 2 ;;
    --root) ROOT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
if [[ -z "$DAY" ]]; then
  echo "usage: run-cycle.sh --day <name> [--root /data/fixtures]" >&2
  exit 2
fi
java -jar /opt/archives/target/circulation-batch-1.0.0.jar "$DAY" "$ROOT"
