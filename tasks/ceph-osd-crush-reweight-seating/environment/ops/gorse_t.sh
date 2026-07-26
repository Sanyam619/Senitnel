#!/bin/bash
set -euo pipefail
gorse_t() {
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local sheet="/app/data/crush/crush_map.txt"
  local row g n h w
  mkdir -p "$sv/state"
  declare -A seen=()
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ "$row" == tip\ * ]] || continue
    g=$(sed -n 's/.*gen=\([0-9]*\).*/\1/p' <<<"$row")
    n=$(sed -n 's/.*osd=\([0-9]*\).*/\1/p' <<<"$row")
    h=$(sed -n 's/.*host=\([a-z0-9-]*\).*/\1/p' <<<"$row")
    w=$(sed -n 's/.*wm=\([0-9]*\).*/\1/p' <<<"$row")
    [[ -n "${seen[$n]:-}" ]] && continue
    seen[$n]=1
    printf '%s\n' "$g" >"$sv/state/spine.${n}.gen"
    printf '%s\n' "$w" >"$sv/state/spine.${n}.wm"
    printf '%s\n' "$h" >"$sv/state/spine.${n}.node"
  done <"$sheet"
}
gorse_t
