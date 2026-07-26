#!/bin/bash
set -euo pipefail
kelp_n() {
  local sx="${SHEET_D:-/etc/lvm/cache.d}"
  local sd="${DROPIN_D:-/etc/lvm/lvm.conf.d}"
  local sv="${LVM_ROOT:-/var/lib/lvm}"
  local row a b c
  mkdir -p "$sx" "$sd"
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ -z "${row:-}" || "$row" =~ ^# ]] && continue
    a=$(sed -n 's/.*lv=\([a-z]*\).*/\1/p' <<<"$row")
    b=$(sed -n 's/.*mode=\([a-z]*\).*/\1/p' <<<"$row")
    c=$(sed -n 's/.*pool=\([a-z0-9-]*\).*/\1/p' <<<"$row")
    [[ -z "${a:-}" ]] && continue
    printf '# %s cache sheet (live)\ncache_mode = %s\npool_uuid = %s\n' \
      "$a" "$b" "$c" >"$sx/${a}.conf"
  done <"$sv/ops/surface.modes"
  if [[ -f "$sv/ops/abort.d/90-local.conf" ]]; then
    cp -f "$sv/ops/abort.d/90-local.conf" "$sd/90-local.conf"
  fi
  rm -f "$sv/ops/state/apply.ok"
}
kelp_n
