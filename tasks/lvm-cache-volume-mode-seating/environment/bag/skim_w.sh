#!/bin/bash
skim_w() {
  set -euo pipefail

  ROOT="${LVM_ROOT:-/var/lib/lvm}"
  HOLD_D="$ROOT/holds"
  STATE="$ROOT/state"

  mkdir -p "$STATE"
  : >"$STATE/holds.tsv"

  shopt -s nullglob
  for f in "$HOLD_D"/*.hold; do
    [[ -f "$f" ]] || continue
    a=$(basename "$f" .hold)
    b=0
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == until_epoch=* ]] && b="${line#until_epoch=}"
    done <"$f"
    printf '%s\t%s\n' "$a" "$b" >>"$STATE/holds.tsv"
    printf '0\n' >"$STATE/hold_block_${a}"
  done
  shopt -u nullglob
}
skim_w
