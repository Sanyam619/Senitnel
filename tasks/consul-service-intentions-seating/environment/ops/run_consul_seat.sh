#!/bin/bash
set -euo pipefail

OPS="${CS_OPS:-/var/lib/consul/ops}"
ETC="${CS_ETC:-/etc/consul.d}"
LIST="${PHASE_LIST:-/app/ops/run.list}"

mkdir -p /output "$OPS/live" "$OPS/state" "$ETC/conf.d" "$ETC/intentions.d" \
  "$ETC/runtime" /var/run/consul /var/log/consul

exec 9>/var/run/consul/seat.lock
flock 9

while IFS= read -r phase || [[ -n "${phase:-}" ]]; do
  phase="${phase%%#*}"
  phase="$(echo "$phase" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$phase" ]] && continue
  [[ -x "$phase" ]] || chmod +x "$phase" 2>/dev/null || true
  bash "$phase"
done <"$LIST"
