#!/bin/bash
set -euo pipefail
sock_v() {
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  local sheet="${REPLICA_SHEET:-/etc/redis/replica.list}"
  local out="$sv/state/replicas.tsv"
  mkdir -p "$sv/state"
  : >"$out"
  while IFS='|' read -r m addr reported lag || [[ -n "${m:-}" ]]; do
    [[ -z "${m:-}" || "$m" =~ ^# ]] && continue
    printf '%s\t%s\t%s\t1\n' "$m" "$addr" "$lag" >>"$out"
  done <"$sheet"
}
sock_v
