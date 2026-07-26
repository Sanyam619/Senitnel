#!/bin/bash
set -euo pipefail
knit_q() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  local surf="$sq_y/surface"
  mkdir -p "$sq_x/peers.d" "$sq_y/state"
  if [[ -d "$surf/peers.d" ]]; then
    cp -a "$surf/peers.d/." "$sq_x/peers.d/"
  fi
  if [[ -d "$surf/tips" ]]; then
    cp -a "$surf/tips/." "$sq_y/state/"
  fi
  date +%s >"$sq_y/state/probe.stamp"
}
knit_q
