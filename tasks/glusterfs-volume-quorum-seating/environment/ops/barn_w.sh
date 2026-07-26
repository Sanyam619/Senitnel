#!/bin/bash
set -euo pipefail
barn_w() {
  local ROOT="${GLUSTER_ROOT:-/var/lib/glusterd}"
  local LIVE_FLOORS="${LIVE_FLOORS:-/etc/glusterfs/floors}"
  local ROSTER="${ROSTER:-/etc/glusterfs/roster.list}"
  local STATE="$ROOT/state"
  local a b c

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
    printf '1\n' >"$STATE/quorum_${a}"
  done <"$ROSTER"
}
barn_w
