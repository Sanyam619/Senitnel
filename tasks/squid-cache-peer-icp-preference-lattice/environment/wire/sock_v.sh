#!/bin/bash
set -euo pipefail
sock_v() {
  local sq_x="${SQ_ETC:-/etc/squid}"
  local sq_y="${SQ_VAR:-/var/lib/squid}"
  mkdir -p "$sq_y/state" "$sq_x/peers.d"
  : >"$sq_y/state/selected.set"
  local name
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "$name" ]] && continue
    echo "$name" >>"$sq_y/state/selected.set"
  done <"$sq_x/roster.list"
  date +%s >"$sq_y/state/probe.stamp"
}
sock_v
