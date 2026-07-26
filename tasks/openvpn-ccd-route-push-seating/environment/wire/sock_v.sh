#!/bin/bash
set -euo pipefail
sock_v() {
  local ov_x="${OV_ETC:-/etc/openvpn}"
  local ov_y="${OV_VAR:-/var/lib/openvpn}"
  mkdir -p "$ov_y/state" "$ov_x/ccd"
  : >"$ov_y/state/pushed.set"
  local name
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "$name" ]] && continue
    echo "$name" >>"$ov_y/state/pushed.set"
  done <"$ov_x/server/roster.list"
  date +%s >"$ov_y/state/probe.stamp"
}
sock_v
