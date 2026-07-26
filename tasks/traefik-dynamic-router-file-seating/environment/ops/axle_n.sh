#!/bin/bash
set -euo pipefail
axle_n() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  mkdir -p "$trf_y/ops/state"
  local floor name val
  for floor in "$trf_x"/floors/*.floor; do
    [[ -f "$floor" ]] || continue
    name=$(basename "$floor" .floor)
    val=$(tr -d ' \t\r\n' <"$floor")
    printf '%s\n' "$val" >"$trf_y/ops/state/tip_${name}.gen"
  done
}
axle_n
