#!/bin/bash
set -euo pipefail
axle_n() {
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  local mx="${MONITOR_D:-/etc/redis/monitors.d}"
  local rl="${ROSTER:-/etc/redis/roster.list}"
  local name host
  mkdir -p "$sv/state"
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "${name:-}" || "$name" =~ ^# ]] && continue
    host=$(sed -n 's/^sentinel monitor '"$name"' \([^ ]*\).*/\1/p' "$mx/${name}.conf" | head -n1)
    [[ -z "${host:-}" ]] && host="0.0.0.0"
    printf '%s:6379\n' "$host" >"$sv/state/tip_${name}.addr"
    printf '2\n' >"$sv/state/tip_${name}.gen"
    printf '2\n' >"$sv/state/pub_${name}.gen"
    printf '0\n' >"$sv/state/elig_${name}"
  done <"$rl"
  printf '3\n' >"$sv/state/gen.live"
}
axle_n
