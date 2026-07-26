#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
PREF_D="${BTRFS_PREF_D:-/etc/btrfs/pref.d}"
ARMED="$ROOT/meta/pref.armed"

mkdir -p "$ROOT/meta"

mode="strict-gt"
shopt -s nullglob
for f in "$PREF_D"/*.conf; do
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    if [[ "$line" == mode=* ]]; then
      mode="${line#mode=}"
      printf '%s\n' "$mode" >"$ARMED"
      exit 0
    fi
  done <"$f"
done
shopt -u nullglob

printf '%s\n' "$mode" >"$ARMED"
