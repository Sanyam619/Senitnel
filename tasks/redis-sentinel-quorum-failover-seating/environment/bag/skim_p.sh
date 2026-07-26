#!/bin/bash
set -euo pipefail
skim_p() {
  local sv="${REDIS_ROOT:-/var/lib/redis}"
  local rl="${ROSTER:-/etc/redis/roster.list}"
  local qfile="$sv/ops/surface.quorum"
  local want online_n name
  want=$(sed -n 's/^quorum=\([0-9]*\).*/\1/p' "$qfile" | head -n1)
  online_n=$(sed -n 's/^online=\(.*\)/\1/p' "$qfile" | head -n1 | tr ',' '\n' | grep -c . || true)
  mkdir -p "$sv/state"
  printf '%s\n' "$want" >"$sv/state/quorum.want"
  printf '%s\n' "$online_n" >"$sv/state/quorum.online"
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "${name:-}" || "$name" =~ ^# ]] && continue
    if [[ "$online_n" -ge "$want" && "$want" -gt 0 ]]; then
      printf '1\n' >"$sv/state/quorum_${name}"
    else
      printf '0\n' >"$sv/state/quorum_${name}"
    fi
  done <"$rl"
}
skim_p
