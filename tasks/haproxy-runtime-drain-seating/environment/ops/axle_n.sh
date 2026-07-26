#!/bin/bash
set -euo pipefail
axle_n() {
  local hap_x="${HAP_ETC:-/etc/haproxy}"
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  mkdir -p "$hap_y/state"
  local floor name val
  for floor in "$hap_x"/floors/*.floor; do
    [[ -f "$floor" ]] || continue
    name=$(basename "$floor" .floor)
    val=$(tr -d ' \t\r\n' <"$floor")
    printf '%s\n' "$val" >"$hap_y/state/tip_${name}.gen"
  done
}
axle_n
