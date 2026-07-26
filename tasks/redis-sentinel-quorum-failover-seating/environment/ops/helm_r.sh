#!/bin/bash
set -euo pipefail
helm_r() {
  local mx="${MONITOR_D:-/etc/redis/monitors.d}"
  local sd="${DROPIN_D:-/etc/redis/sentinel.d}"
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  local row a b
  mkdir -p "$mx" "$sd"
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ -z "${row:-}" || "$row" =~ ^# ]] && continue
    a=$(sed -n 's/^\([a-z]*\)=.*/\1/p' <<<"$row")
    b=$(sed -n 's/^[a-z]*=\(.*\)/\1/p' <<<"$row")
    [[ -z "${a:-}" || -z "${b:-}" ]] && continue
    host="${b%%:*}"
    printf 'sentinel monitor %s %s 6379 2\nsentinel down-after-milliseconds %s 5000\n' \
      "$a" "$host" "$a" >"$mx/${a}.conf"
  done <"$sv/ops/surface.monitors"
  if [[ -f "$sv/ops/abort.d/90-local.conf" ]]; then
    cp -f "$sv/ops/abort.d/90-local.conf" "$sd/90-local.conf"
  fi
  rm -f "$sv/ops/state/apply.ok"
  cp -f "$sv/ops/surface.quorum" "$sv/state/quorum.sheet"
}
helm_r
