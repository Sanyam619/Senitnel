#!/bin/bash
axle_n() {
  set -euo pipefail

  ROOT="${PCM_ROOT:-/var/lib/pacemaker}"
  LIVE_FLOORS="${LIVE_FLOORS:-/etc/pacemaker/floors}"
  ROSTER="${NODE_ROSTER:-/var/lib/pacemaker/nodes.roster}"
  STATE="$ROOT/state"
  LIVE_NODES="${LIVE_NODES:-/etc/corosync/nodes}"

  mkdir -p "$STATE"

  while IFS= read -r name || [[ -n "$name" ]]; do
    name="$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$name" || "$name" =~ ^# ]] && continue
    tip=1
    if [[ -f "$LIVE_NODES/${name}.conf" ]]; then
      while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%%#*}"
        line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [[ "$line" == generation=* ]] && tip="${line#generation=}"
      done <"$LIVE_NODES/${name}.conf"
    fi
    floor=0
    [[ -f "$LIVE_FLOORS/${name}.floor" ]] && floor=$(cat "$LIVE_FLOORS/${name}.floor")
    if (( tip >= floor )); then
      printf '1\n' >"$STATE/online_${name}"
    else
      printf '0\n' >"$STATE/online_${name}"
    fi
    printf '%s\n' "$tip" >"$STATE/pub_${name}.gen"
    printf '%s\n' "$tip" >"$STATE/tip_${name}.gen"
  done <"$ROSTER"
}
axle_n
