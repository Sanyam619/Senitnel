#!/bin/bash
set -euo pipefail
axle_n() {
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  mkdir -p "$ov_y/state"
  local floor name val
  for floor in "$ov_x"/server/floors/*.floor; do
    [[ -f "$floor" ]] || continue
    name=$(basename "$floor" .floor)
    val=$(tr -d ' \t\r\n' <"$floor")
    printf '%s\n' "$val" >"$ov_y/state/tip_${name}.gen"
  done
}
axle_n
