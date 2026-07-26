#!/bin/bash
skim_z() {
  set -euo pipefail

  ROOT="${AUTO_ROOT:-/var/lib/autofs}"
  HOLD_D="$ROOT/holds"
  STATE="$ROOT/state"
  ROSTER="${ROSTER:-/etc/autofs/roster.list}"

  mkdir -p "$STATE"
  : >"$STATE/holds.tsv"

  shopt -s nullglob
  for f in "$HOLD_D"/*.hold; do
    [[ -f "$f" ]] || continue
    key=$(basename "$f" .hold)
    until_epoch=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == until_epoch=* ]] && until_epoch="${line#until_epoch=}"
    done <"$f"
    printf '%s\t%s\topen\n' "$key" "$until_epoch" >>"$STATE/holds.tsv"
    printf '0\n' >"$STATE/hold_block_${key}"
  done
  shopt -u nullglob
}
skim_z
