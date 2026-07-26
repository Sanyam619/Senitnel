#!/bin/bash
set -euo pipefail

OPS="${KV_OPS:-/var/lib/keepalived/ops}"
ETC="${KV_ETC:-/etc/keepalived}"
LIST="${PHASE_LIST:-/app/ops/run.list}"

mkdir -p /output "$OPS/live" "$OPS/state" "$ETC/conf.d" "$ETC/runtime" \
  /var/run/keepalived /var/log/keepalived

exec 9>/var/run/keepalived/seat.lock
flock 9

while IFS= read -r phase || [[ -n "${phase:-}" ]]; do
  phase="${phase%%#*}"
  phase="$(echo "$phase" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$phase" ]] && continue
  [[ -x "$phase" ]] || chmod +x "$phase" 2>/dev/null || true
  bash "$phase"
done <"$LIST"
