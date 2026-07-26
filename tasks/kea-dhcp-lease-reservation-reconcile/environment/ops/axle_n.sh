#!/bin/bash
set -euo pipefail
axle_n() {
  local kea_x="${KEA_ETC:-/etc/kea}"
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  mkdir -p "$kea_y/state"
  local floor name val
  for floor in "$kea_x"/floors/*.floor; do
    [[ -f "$floor" ]] || continue
    name=$(basename "$floor" .floor)
    val=$(tr -d ' \t\r\n' <"$floor")
    printf '%s\n' "$val" >"$kea_y/state/tip_${name}.gen"
  done
}
axle_n
