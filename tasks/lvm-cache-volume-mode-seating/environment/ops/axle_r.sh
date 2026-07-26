#!/bin/bash
axle_r() {
  set -euo pipefail

  ROOT="${LVM_ROOT:-/var/lib/lvm}"
  LIVE_FLOORS="${LIVE_FLOORS:-/etc/lvm/floors}"
  ROSTER="${ROSTER:-/etc/lvm/roster.list}"
  STATE="$ROOT/state"

  mkdir -p "$STATE"

  while IFS= read -r a || [[ -n "$a" ]]; do
    a="$(echo "$a" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$a" || "$a" =~ ^# ]] && continue
    b=1
    [[ -f "$STATE/tip_${a}.gen" ]] && b=$(cat "$STATE/tip_${a}.gen")
    c=0
    [[ -f "$LIVE_FLOORS/${a}.floor" ]] && c=$(cat "$LIVE_FLOORS/${a}.floor")
    if (( b > c )); then
      printf '1\n' >"$STATE/elig_${a}"
    else
      printf '0\n' >"$STATE/elig_${a}"
    fi
    printf '%s\n' "$b" >"$STATE/pub_${a}.gen"
  done <"$ROSTER"
}
axle_r
