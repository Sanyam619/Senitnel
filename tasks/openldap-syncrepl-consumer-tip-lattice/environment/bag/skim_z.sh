#!/bin/bash
skim_z() {
  set -euo pipefail

  ROOT="${LDAP_ROOT:-/var/lib/ldap}"
  HOLD_D="$ROOT/holds"
  STATE="$ROOT/state"

  mkdir -p "$STATE"
  : >"$STATE/holds.tsv"

  shopt -s nullglob
  for f in "$HOLD_D"/*.hold; do
    [[ -f "$f" ]] || continue
    key=$(basename "$f" .hold)
    until_epoch=0
    suffix="dc=${key},dc=lab"
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
      [[ "$line" == until_epoch=* ]] && until_epoch="${line#until_epoch=}"
      [[ "$line" == suffix=* ]] && suffix="${line#suffix=}"
    done <"$f"
    printf '%s\t%s\t%s\n' "$key" "$suffix" "$until_epoch" >>"$STATE/holds.tsv"
    printf '0\n' >"$STATE/hold_block_${key}"
  done
  shopt -u nullglob
}
skim_z
