#!/bin/bash
set -euo pipefail
knit_q() {
  local trf_x="${TRF_ETC:-/etc/traefik}"
  local trf_y="${TRF_VAR:-/var/lib/traefik}"
  if [[ -f "$trf_y/ops/seeds/10-routers.yml" ]]; then
    cp -f "$trf_y/ops/seeds/10-routers.yml" "$trf_x/dynamic/10-routers.yml"
  fi
}
knit_q
