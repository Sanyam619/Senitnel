#!/bin/bash
set -euo pipefail

QEMU_DIR="${QEMU_DIR:-/etc/libvirt/qemu}"
STORAGE_DIR="${STORAGE_DIR:-/etc/libvirt/storage}"
OPS_DIR="${OPS_DIR:-/var/lib/libvirt/ops}"
ROSTER="${SEAT_ROSTER:-$QEMU_DIR/seat.roster}"
PLAN="${SEAT_PLAN:-$OPS_DIR/seating.plan}"

mkdir -p "$OPS_DIR"
: > "$PLAN"

declare -A seen=()
while IFS='|' read -r domain target pool volume || [[ -n "$domain" ]]; do
  [[ -z "$pool" || "$domain" == \#* ]] && continue
  [[ -n "${seen[$pool]:-}" ]] && continue
  seen[$pool]=1
  xml="$STORAGE_DIR/pool_${pool}.xml"
  [[ -f "$xml" ]] || continue
  uuid="$(grep -oP '(?<=<uuid>)[^<]+' "$xml" | head -n1 | tr -d '[:space:]')"
  path="$(grep -oP '(?<=<path>)[^<]+' "$xml" | head -n1 | tr -d '[:space:]')"
  printf '%s\t%s\t%s\n' "$pool" "$uuid" "$path" >> "$PLAN"
done < "$ROSTER"
