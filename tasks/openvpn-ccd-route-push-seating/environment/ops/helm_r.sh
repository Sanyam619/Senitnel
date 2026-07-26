#!/bin/bash
set -euo pipefail
helm_r() {
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  local abort_pkg="$ov_y/ops/abort.d/90-local.conf"
  local live_dropin="$ov_x/server/conf.d/90-local.conf"
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$ov_y/state/cutover.ok"
}
helm_r
