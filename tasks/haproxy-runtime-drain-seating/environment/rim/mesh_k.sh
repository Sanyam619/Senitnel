#!/bin/bash
set -euo pipefail
mesh_k() {
  local hap_x="${HAP_ETC:-/etc/haproxy}"
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  mkdir -p "$hap_y/state"
  local eff="$hap_y/state/effective.conf"
  : >"$eff"
  local first
  first=$(find "$hap_x/conf.d" -type f -name '*.cfg' | sort | head -n1 || true)
  if [[ -n "$first" && -f "$first" ]]; then
    cat "$first" >"$eff"
  fi
}
mesh_k
