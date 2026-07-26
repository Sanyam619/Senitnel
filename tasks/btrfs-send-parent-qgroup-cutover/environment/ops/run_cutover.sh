#!/bin/bash
set -euo pipefail
export BTRFS_ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
export BTRFS_SEAL="${BTRFS_SEAL:-/etc/btrfs/pool.seal}"
export LANE_ROSTER="${LANE_ROSTER:-/etc/btrfs/lane.roster}"
export BTRFS_PREF_D="${BTRFS_PREF_D:-/etc/btrfs/pref.d}"
export LEASE_DIR="${LEASE_DIR:-/var/run/btrfs}"
export LANE_OUT="${LANE_OUT:-/output/lanes}"
export SEND_REPORT="${SEND_REPORT:-/output/send-report.json}"
export BTRFS_JOURNAL="${BTRFS_JOURNAL:-$BTRFS_ROOT/ops/journal.jsonl}"
export BTRFS_DESKD_ENV="${BTRFS_DESKD_ENV:-/etc/btrfs/deskd.env}"

mkdir -p "$BTRFS_ROOT" "$LEASE_DIR" "$BTRFS_ROOT/attach" \
  "$(dirname "$SEND_REPORT")" "$LANE_OUT" "$BTRFS_ROOT/meta" /var/log/btrfs

# Serialize concurrent cutovers on a shared lock so attach/tip-map seats stay consistent.
exec 9>"$LEASE_DIR/cutover.lock"
flock 9

/app/wire/knit_p.sh
/app/rim/fold_q.sh
/app/ops/axle_j.sh
/app/bag/slot_w.sh
/app/deck/hold_c.sh
/app/dock/link_v.sh
/app/ops/deskd
exec /app/bin/bops
