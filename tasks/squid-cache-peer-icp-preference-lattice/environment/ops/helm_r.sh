#!/bin/bash
set -euo pipefail
helm_r() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  local abort_pkg="$sq_y/ops/abort.d/90-local.cfg"
  local live_dropin="$sq_x/conf.d/90-local.cfg"
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$sq_y/state/cutover.ok"
}
helm_r
