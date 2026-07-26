#!/bin/bash
axle_y() {
  set -euo pipefail

  ROOT="${LDAP_ROOT:-/var/lib/ldap}"
  LIVE_FLOORS="${LIVE_FLOORS:-/etc/ldap/floors}"
  ROSTER="${ROSTER:-/etc/ldap/roster.list}"
  STATE="$ROOT/state"

  mkdir -p "$STATE"

  while IFS=$'\t' read -r name suffix || [[ -n "$name" ]]; do
    name="$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$name" || "$name" =~ ^# ]] && continue
    csn="missing"
    [[ -f "$ROOT/${name}/contextCSN" ]] && csn=$(tr -d '[:space:]' <"$ROOT/${name}/contextCSN")
    tip=1
    [[ -f "$STATE/tip_${name}.gen" ]] && tip=$(tr -d '[:space:]' <"$STATE/tip_${name}.gen")
    floor=0
    [[ -f "$LIVE_FLOORS/${name}.floor" ]] && floor=$(tr -d '[:space:]' <"$LIVE_FLOORS/${name}.floor")
    if (( tip > floor )); then
      printf '1\n' >"$STATE/elig_${name}"
    else
      printf '0\n' >"$STATE/elig_${name}"
    fi
    printf '%s\n' "$tip" >"$STATE/pub_${name}.gen"
    printf '%s\n' "$csn" >"$STATE/pub_${name}.csn"
  done <"$ROSTER"
}
axle_y
