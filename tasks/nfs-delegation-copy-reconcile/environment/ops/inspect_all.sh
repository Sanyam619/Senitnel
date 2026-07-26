#!/bin/bash
set -euo pipefail

# inspect_all.sh — walk every episode under /app/data/episodes and run
# the read-only inspector on it. Useful for a first-pass look at what each
# episode's journals actually contain.

INSPECTOR="/app/bin/nfsr-inspect"
EPDIR="/app/data/episodes"

if [[ ! -x "$INSPECTOR" ]]; then
  echo "inspect_all: $INSPECTOR is not executable" >&2
  exit 1
fi

for ep in "$EPDIR"/*/; do
  name="$(basename "$ep")"
  echo "==================== $name ===================="
  "$INSPECTOR" "$ep"
  echo
done
