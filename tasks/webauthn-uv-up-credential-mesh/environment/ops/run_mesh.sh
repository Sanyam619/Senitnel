#!/bin/bash
# run_mesh.sh — arm live ceremony helpers, then publish via prebuilt trusteval.
# Does not rebuild from source; binaries are image-installed under /app/bin.

set -euo pipefail

APP=/app
OUT="${1:-/output/ceremony-ledger.json}"

mkdir -p /output \
  /etc/ceremony/reconcile.d \
  /var/lib/ceremony/state \
  /var/lib/ceremony/ops/abort.d

bash "$APP/ops/seat_uv.sh"
bash "$APP/ops/axle_hold.sh"
bash "$APP/ops/knit_stream.sh"
bash "$APP/ops/fold_d.sh"
bash "$APP/ops/emit_mesh.sh" "$OUT"
