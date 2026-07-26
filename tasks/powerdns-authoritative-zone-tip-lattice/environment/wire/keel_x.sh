#!/bin/bash
set -euo pipefail
keel_x() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  local surf="$pd_y/surface"
  mkdir -p "$pd_x/zones.d" "$pd_x/serials" "$pd_y/state"
  if [[ -d "$surf/zones.d" ]]; then
    cp -a "$surf/zones.d/." "$pd_x/zones.d/"
  fi
  if [[ -d "$surf/tips" ]]; then
    cp -a "$surf/tips/." "$pd_y/state/"
  fi
  if [[ -d "$surf/serials" ]]; then
    cp -a "$surf/serials/." "$pd_x/serials/"
  fi
  date +%s >"$pd_y/state/probe.stamp"
}
keel_x
