#!/bin/bash
axle_y() {
  set -euo pipefail

  ROOT="${AUTO_ROOT:-/var/lib/autofs}"
  LIVE_FLOORS="${LIVE_FLOORS:-/etc/autofs/floors}"
  ROSTER="${ROSTER:-/etc/autofs/roster.list}"
  STATE="$ROOT/state"

  mkdir -p "$STATE"

  while IFS= read -r name || [[ -n "$name" ]]; do
    name="$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$name" || "$name" =~ ^# ]] && continue
    tip=1
    [[ -f "$STATE/tip_${name}.gen" ]] && tip=$(cat "$STATE/tip_${name}.gen")
    floor=0
    [[ -f "$LIVE_FLOORS/${name}.floor" ]] && floor=$(cat "$LIVE_FLOORS/${name}.floor")
    if (( tip > floor )); then
      printf '1\n' >"$STATE/elig_${name}"
    else
      printf '0\n' >"$STATE/elig_${name}"
    fi
    printf '%s\n' "$tip" >"$STATE/pub_${name}.gen"
  done <"$ROSTER"
}
axle_y
