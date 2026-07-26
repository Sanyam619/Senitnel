#!/bin/bash
set -euo pipefail
sock_v() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  mkdir -p "$pf_y/state"
  : >"$pf_y/state/active.set"
  local name
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "$name" ]] && continue
    echo "$name" >>"$pf_y/state/active.set"
  done <"$pf_x/roster.list"
  date +%s >"$pf_y/state/probe.stamp"
}
sock_v
