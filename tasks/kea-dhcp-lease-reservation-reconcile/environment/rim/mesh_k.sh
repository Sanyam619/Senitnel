#!/bin/bash
set -euo pipefail
mesh_k() {
  local kea_x="${KEA_ETC:-/etc/kea}"
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  mkdir -p "$kea_y/state"
  local eff="$kea_y/state/effective.conf"
  : >"$eff"
  local first
  first=$(find "$kea_x/kea-dhcp4.d" -type f -name '*.conf' | sort | head -n1 || true)
  if [[ -n "$first" && -f "$first" ]]; then
    cat "$first" >"$eff"
  fi
  : >"$kea_y/state/shadowed.ips"
}
mesh_k
