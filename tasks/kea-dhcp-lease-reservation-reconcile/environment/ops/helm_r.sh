#!/bin/bash
set -euo pipefail
helm_r() {
  local kea_x="${KEA_ETC:-/etc/kea}"
  local kea_y="${KEA_VAR:-/var/lib/kea}"
  local abort_pkg="$kea_y/ops/abort.d/90-local.conf"
  local live_dropin="$kea_x/kea-dhcp4.d/90-local.conf"
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$kea_y/state/cutover.ok"
}
helm_r
