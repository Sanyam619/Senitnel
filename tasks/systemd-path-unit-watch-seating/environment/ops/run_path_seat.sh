#!/bin/bash
set -euo pipefail

OPS="${SYS_OPS:-/var/lib/systemd/ops}"
ETC="${SYS_ETC:-/etc/systemd/system}"
LIST="${PHASE_LIST:-/app/ops/run.list}"

mkdir -p /output "$OPS/live" "$OPS/state" "$ETC" \
  /run/systemd/watch-seat /var/run/systemd-seat /var/log/watch-seat

exec 9>/var/run/systemd-seat/seat.lock
flock 9

while IFS= read -r phase || [[ -n "${phase:-}" ]]; do
  phase="${phase%%#*}"
  phase="$(echo "$phase" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [[ -z "$phase" ]] && continue
  [[ -x "$phase" ]] || chmod +x "$phase" 2>/dev/null || true
  bash "$phase"
done <"$LIST"
