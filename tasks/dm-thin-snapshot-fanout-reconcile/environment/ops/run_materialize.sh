#!/bin/bash
set -euo pipefail
export POOL_ROOT="${POOL_ROOT:-/var/lib/pool}"
export POOL_SEAL="${POOL_SEAL:-/etc/pool/pool.seal}"
export DRILL_ROSTER="${DRILL_ROSTER:-/etc/pool/drill.roster}"
export POOL_PREF_D="${POOL_PREF_D:-/etc/pool/pref.d}"
export LEASE_DIR="${LEASE_DIR:-/var/run/pool}"
export ORIGIN_ROOT="${ORIGIN_ROOT:-/var/lib/pool/origin_stage}"
export SEAL_GEN_FILE="${SEAL_GEN_FILE:-/var/lib/pool/meta/seal_gen.arm}"
export DRILL_OUT="${DRILL_OUT:-/output/drills}"
export FANOUT_REPORT="${FANOUT_REPORT:-/output/fanout-report.json}"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-/app/lib}"

mkdir -p "$POOL_ROOT" "$LEASE_DIR" "$ORIGIN_ROOT" "$(dirname "$FANOUT_REPORT")" "$DRILL_OUT"

/app/ops/fold_k.sh
/app/ops/pref_a.sh
/app/ops/skim_x.sh
/app/ops/hold_m.sh
/app/ops/emit_h.sh
exec /app/bin/matfan
