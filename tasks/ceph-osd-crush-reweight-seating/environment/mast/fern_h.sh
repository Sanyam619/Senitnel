#!/bin/bash
set -euo pipefail
fern_h() {
  local sx="${SD_ETC:-/etc/ceph}"
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local row node tally=0 f n
  declare -A blocked=()
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ -z "${row:-}" ]] && continue
    node=$(sed -n 's/.*"host": "\([a-z0-9-]*\)".*/\1/p' <<<"$row")
    [[ -n "$node" ]] && blocked[$node]=1
  done <"$sv/window.jsonl"
  for f in "$sx"/reweight.d/osd.*.conf; do
    n=${f##*/osd.}
    n=${n%.conf}
    [[ -f "$sv/state/knot.${n}.flag" ]] && continue
    node=$(cat "$sv/state/spine.${n}.node" 2>/dev/null || echo "")
    [[ -n "$node" && -n "${blocked[$node]:-}" ]] && continue
    tally=$((tally + 1))
  done
  rm -f "$sv/state"/mesh.*.flag
  local name size
  for f in "$sx"/pools.d/*.conf; do
    while IFS= read -r row || [[ -n "${row:-}" ]]; do
      if [[ "$row" =~ ^\[pool\ \"([a-z-]+)\"\]$ ]]; then
        name="${BASH_REMATCH[1]}"
      elif [[ "$row" =~ ^size\ =\ ([0-9]+)$ && -n "${name:-}" ]]; then
        size="${BASH_REMATCH[1]}"
        if (( tally < size )); then
          printf '1\n' >"$sv/state/mesh.${name}.flag"
        else
          printf '0\n' >"$sv/state/mesh.${name}.flag"
        fi
      fi
    done <"$f"
  done
}
fern_h
