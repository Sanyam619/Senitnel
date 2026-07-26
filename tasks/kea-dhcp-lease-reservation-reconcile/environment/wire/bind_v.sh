#!/bin/bash
set -euo pipefail
bind_v() {
  local kea_x="${KEA_ETC:-/etc/kea}"
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  local kea_z="${KEA_RUN:-/var/run/kea}"
  mkdir -p "$kea_z" "$kea_y/state/pool_ok"
  rm -f "$kea_y/state/pool_ok"/*
  local sid pool
  while IFS= read -r sid || [[ -n "${sid:-}" ]]; do
    [[ -z "${sid:-}" ]] && continue
    pool=$(tr -d ' \t\r\n' <"$kea_x/pools/${sid}.pool" 2>/dev/null || echo "")
    printf '%s\n' "$pool" >"$kea_y/state/pool_ok/${sid}.cidr"
  done <"$kea_x/roster.list"
  printf '0\n' >"$kea_z/prefer.applied"
}
bind_v
