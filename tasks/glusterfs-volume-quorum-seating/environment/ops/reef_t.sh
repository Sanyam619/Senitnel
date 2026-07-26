#!/bin/bash
set -euo pipefail
reef_t() {
  local bx="${BRICK_D:-/etc/glusterfs/bricks.d}"
  local sd="${DROPIN_D:-/etc/glusterfs/glusterd.d}"
  local sv="${GLUSTER_ROOT:-/var/lib/glusterd}"
  local row a b
  mkdir -p "$bx" "$sd"
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ -z "${row:-}" || "$row" =~ ^# ]] && continue
    a=$(sed -n 's/.*vol=\([a-z]*\).*/\1/p' <<<"$row")
    b=$(sed -n 's/.*bricks=\([^ ]*\).*/\1/p' <<<"$row")
    [[ -z "${a:-}" ]] && continue
    tr ',' '\n' <<<"$b" >"$bx/${a}.bricks"
  done <"$sv/ops/surface.bricks"
  if [[ -f "$sv/ops/abort.d/90-local.conf" ]]; then
    cp -f "$sv/ops/abort.d/90-local.conf" "$sd/90-local.conf"
  fi
  rm -f "$sv/ops/state/apply.ok"
}
reef_t
