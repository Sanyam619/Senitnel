#!/bin/bash
set -euo pipefail
axle_n() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  mkdir -p "$sq_y/state"
  local floor name val
  for floor in "$sq_x"/floors/*.floor; do
    [[ -f "$floor" ]] || continue
    name=$(basename "$floor" .floor)
    val=$(tr -d ' \t\r\n' <"$floor")
    printf '%s\n' "$val" >"$sq_y/state/tip_${name}.gen"
  done
}
axle_n
