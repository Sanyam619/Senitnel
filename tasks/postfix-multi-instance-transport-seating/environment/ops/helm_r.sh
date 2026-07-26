#!/bin/bash
set -euo pipefail
helm_r() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  local abort_pkg="$pf_y/ops/abort.d/90-local.cf"
  local live_dropin="$pf_x/master.d/90-local.cf"
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$pf_y/state/cutover.ok"
}
helm_r
