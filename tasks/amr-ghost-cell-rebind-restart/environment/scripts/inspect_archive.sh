#!/usr/bin/env bash
set -euo pipefail
cd /app
shopt -s nullglob
for blob in /app/data/archive_cycle_*.blob; do
  printf '%s %s bytes\n' "$blob" "$(wc -c < "$blob")"
done
