#!/bin/bash
set -euo pipefail
helm_r() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  local abort_pkg="$trf_y/ops/abort.d/90-abort.yml"
  local live_dropin="$trf_x/dynamic/90-local.yml"
  if [[ -f "$abort_pkg" ]]; then
    cp -f "$abort_pkg" "$live_dropin"
  fi
  rm -f "$trf_y/ops/state/cutover.ok"
}
helm_r
