#!/bin/bash
set -euo pipefail
knit_q() {
  local pf_x="${PF_ETC:-/etc/postfix}"
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  local surf="$pf_y/surface"
  mkdir -p "$pf_y/state" "$pf_y/ops/maps"
  if [[ -d "$surf/tips" ]]; then
    cp -a "$surf/tips/." "$pf_y/state/"
  fi
  if [[ -f "$surf/maps/nexthop.prefer" ]]; then
    cp -f "$surf/maps/nexthop.prefer" "$pf_y/ops/maps/nexthop.prefer"
  fi
  if [[ -d "$surf/main.d" ]]; then
    local name
    while IFS= read -r name || [[ -n "${name:-}" ]]; do
      [[ -z "$name" ]] && continue
      if [[ -f "$surf/main.d/$name/main.cf" ]]; then
        mkdir -p "/etc/postfix-${name}"
        cp -f "$surf/main.d/$name/main.cf" "/etc/postfix-${name}/main.cf"
      fi
    done <"$pf_x/roster.list"
  fi
  date +%s >"$pf_y/state/probe.stamp"
}
knit_q
