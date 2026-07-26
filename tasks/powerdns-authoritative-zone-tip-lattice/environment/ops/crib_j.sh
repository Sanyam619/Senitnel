#!/bin/bash
set -euo pipefail
crib_j() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  local abort_pkg="$pd_y/ops/abort.d/90-local.conf"
  local live_dropin="$pd_x/pdns.d/90-local.conf"
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$pd_y/state/cutover.ok"
}
crib_j
