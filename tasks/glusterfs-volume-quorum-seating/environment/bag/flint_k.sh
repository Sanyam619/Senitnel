#!/bin/bash
set -euo pipefail
flint_k() {
  local ROOT="${GLUSTER_ROOT:-/var/lib/glusterd}"
  local HOLD_D="$ROOT/holds"
  local STATE="$ROOT/state"
  local f a b c line

  mkdir -p "$STATE"
  : >"$STATE/holds.tsv"

  shopt -s nullglob
  for f in "$HOLD_D"/*.hold; do
    [[ -f "$f" ]] || continue
    a=$(basename "$f" .hold)
    b=""
    c=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == brick=* ]] && b="${line#brick=}"
      [[ "$line" == until_epoch=* ]] && c="${line#until_epoch=}"
    done <"$f"
    printf '%s\t%s\t%s\n' "$a" "$b" "$c" >>"$STATE/holds.tsv"
    printf '0\n' >"$STATE/hold_block_${a}"
  done
  shopt -u nullglob
}
flint_k
