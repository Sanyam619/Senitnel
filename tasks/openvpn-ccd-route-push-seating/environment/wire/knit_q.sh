#!/bin/bash
set -euo pipefail
knit_q() {
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  local surf="$ov_y/surface"
  mkdir -p "$ov_x/ccd" "$ov_y/state"
  if [[ -d "$surf/ccd" ]]; then
    cp -a "$surf/ccd/." "$ov_x/ccd/"
  fi
  if [[ -d "$surf/tips" ]]; then
    cp -a "$surf/tips/." "$ov_y/state/"
  fi
  date +%s >"$ov_y/state/probe.stamp"
}
knit_q
