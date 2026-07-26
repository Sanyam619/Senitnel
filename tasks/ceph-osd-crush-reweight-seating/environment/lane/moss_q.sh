#!/bin/bash
set -euo pipefail
moss_q() {
  local sv="${SD_VAR:-/var/lib/ceph/ops}"
  local row n a
  mkdir -p "$sv/state"
  rm -f "$sv/state"/knot.*.flag
  while IFS= read -r row || [[ -n "${row:-}" ]]; do
    [[ -z "${row:-}" ]] && continue
    n=$(sed -n 's/.*"osd": \([0-9]*\).*/\1/p' <<<"$row")
    a=$(sed -n 's/.*"action": "\([a-z]*\)".*/\1/p' <<<"$row")
    [[ -z "$n" || -z "$a" ]] && continue
    if [[ "$a" == "out" ]]; then
      printf '1\n' >"$sv/state/knot.${n}.flag"
    fi
  done <"$sv/record.jsonl"
}
moss_q
