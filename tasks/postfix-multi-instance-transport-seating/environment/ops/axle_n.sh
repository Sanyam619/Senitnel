#!/bin/bash
set -euo pipefail
axle_n() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  mkdir -p "$pf_y/state"
  local floor name val
  for floor in "$pf_x"/floors/*.floor; do
    [[ -f "$floor" ]] || continue
    name=$(basename "$floor" .floor)
    val=$(tr -d ' \t\r\n' <"$floor")
    printf '%s\n' "$val" >"$pf_y/state/tip_${name}.gen"
  done
}
axle_n
