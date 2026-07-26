#!/bin/bash
set -euo pipefail
helm_r() {
  local hap_x="${HAP_ETC:-/etc/haproxy}"
  local hap_y="${HAP_VAR:-/var/lib/haproxy}"
  local abort_pkg="$hap_y/ops/abort.d/90-local.cfg"
  local live_dropin="$hap_x/conf.d/90-local.cfg"
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$hap_y/state/cutover.ok"
}
helm_r
