#!/bin/bash
set -euo pipefail

OPS_DIR="${OPS_DIR:-/var/lib/libvirt/ops}"
PLAN="${SEAT_PLAN:-$OPS_DIR/seating.plan}"
STATE_ROOT="${POOL_STATE_ROOT:-/var/lib/libvirt/storage}"

[[ -f "$PLAN" ]] || exit 0

while IFS=$'\t' read -r pool uuid path || [[ -n "$pool" ]]; do
  [[ -z "$pool" ]] && continue
  dir="$STATE_ROOT/$pool"
  mkdir -p "$dir"
  {
    printf 'state=%s\n' "inactive"
    printf 'path=%s\n' "$path"
  } > "$dir/pool.state"
done < "$PLAN"
