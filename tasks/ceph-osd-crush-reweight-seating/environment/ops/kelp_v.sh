#!/bin/bash
set -euo pipefail
kelp_v() {
  local sx="${SD_ETC:-/etc/ceph}"
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local row n w
  mkdir -p "$sx/reweight.d"
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ -z "${row:-}" || "$row" =~ ^# ]] && continue
    n=${row%% *}
    n=${n#n=}
    w=${row##* }
    w=${w#wm=}
    printf 'reweight_milli = %s\n' "$w" >"$sx/reweight.d/osd.${n}.conf"
  done <"$sv/surface.map"
  rm -f "$sv/state/apply.ok"
}
kelp_v
