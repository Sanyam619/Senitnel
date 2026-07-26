#!/bin/bash
set -euo pipefail
CAND="${CAND_TSV:-/var/lib/keepalived/ops/live/cand.tsv}"
HOLD_D="${HOLD_D:-/var/lib/keepalived/ops/holds}"
CLOCK_F="${CLOCK_F:-/var/lib/keepalived/ops/state/clock.epoch}"
O_F="${ELIG_TSV:-/var/lib/keepalived/ops/live/elig.tsv}"
mkdir -p "$(dirname "$O_F")"
clock=0
[[ -f "$CLOCK_F" ]] && clock="$(tr -d '[:space:]' <"$CLOCK_F")"
: >"$O_F"
[[ -f "$CAND" ]] || exit 0
while IFS=$'\t' read -r name tip rank vrid vip || [[ -n "${name:-}" ]]; do
  [[ -z "${name:-}" ]] && continue
  until=0
  if [[ -f "$HOLD_D/${name}.hold" ]]; then
    until="$(grep -E '^until=' "$HOLD_D/${name}.hold" | head -n1 | cut -d= -f2- | tr -d '[:space:]')"
    until="${until:-0}"
  fi
  held=0
  if [[ "$until" -ge "$clock" ]]; then
    held=1
  fi
  eligible=1
  if [[ "$held" -eq 1 ]]; then
    eligible=0
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$eligible" "$held" "$tip" "0" >>"$O_F"
done <"$CAND"
