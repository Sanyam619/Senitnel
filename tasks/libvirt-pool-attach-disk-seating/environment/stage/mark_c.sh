#!/bin/bash
set -euo pipefail

QEMU_DIR="${QEMU_DIR:-/etc/libvirt/qemu}"
OPS_DIR="${OPS_DIR:-/var/lib/libvirt/ops}"
ROSTER="${SEAT_ROSTER:-$QEMU_DIR/seat.roster}"
PLAN="${SEAT_PLAN:-$OPS_DIR/seating.plan}"
RCPT_DIR="$OPS_DIR/receipts"

mkdir -p "$RCPT_DIR"

declare -A pu=()
if [[ -f "$PLAN" ]]; then
  while IFS=$'\t' read -r pool uuid path || [[ -n "$pool" ]]; do
    [[ -z "$pool" ]] && continue
    pu[$pool]="$uuid"
  done < "$PLAN"
fi

while IFS='|' read -r domain target pool volume || [[ -n "$domain" ]]; do
  [[ -z "$pool" || "$domain" == \#* ]] && continue
  uuid="${pu[$pool]:-}"
  out="$RCPT_DIR/${domain}-${target}.receipt"
  printf '{"pool":"%s","uuid":"%s","volume":"%s"}\n' "$pool" "$uuid" "$volume" > "$out"
done < "$ROSTER"
