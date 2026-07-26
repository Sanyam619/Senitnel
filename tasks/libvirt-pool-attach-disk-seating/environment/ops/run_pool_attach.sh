#!/bin/bash
set -euo pipefail

export QEMU_DIR="${QEMU_DIR:-/etc/libvirt/qemu}"
export STORAGE_DIR="${STORAGE_DIR:-/etc/libvirt/storage}"
export OPS_DIR="${OPS_DIR:-/var/lib/libvirt/ops}"
export POOL_STATE_ROOT="${POOL_STATE_ROOT:-/var/lib/libvirt/storage}"
export SEAT_ROSTER="${SEAT_ROSTER:-/etc/libvirt/qemu/seat.roster}"
export SEAT_PLAN="${SEAT_PLAN:-/var/lib/libvirt/ops/seating.plan}"
export ATTACH_D="${ATTACH_D:-/etc/libvirt/qemu/attach.d}"
export ATTACH_SEAL="${ATTACH_SEAL:-/etc/libvirt/storage/attach.seal}"
export CUTOVER_JOURNAL="${CUTOVER_JOURNAL:-/var/lib/libvirt/ops/cutover.journal}"
export LEASE_DIR="${LEASE_DIR:-/var/run/libvirt}"
export ATTACH_REPORT="${ATTACH_REPORT:-/output/libvirt-attach.json}"

mkdir -p "$OPS_DIR" "$OPS_DIR/receipts" "$POOL_STATE_ROOT" "$ATTACH_D" \
    "$LEASE_DIR" "$(dirname "$ATTACH_REPORT")"

OPS_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE_HOME="${STAGE_HOME:-/app/stage}"

"$OPS_HOME/fold_g.sh"
"$OPS_HOME/pref_k.sh"
"$STAGE_HOME/seat_r.sh"
"$STAGE_HOME/mark_c.sh"
"$OPS_HOME/tidy_v.sh"

exec /app/bin/virtattach
