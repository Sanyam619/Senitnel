#!/bin/bash
set -euo pipefail

# run_recovery.sh — operator entry for post-reboot NFSv4.2 recovery.
# Rebuilds the on-host recovery toolchain from /app/tools and /app/lib
# and runs it against every recorded restart episode under
# /app/data/episodes, writing the post-reboot state report to
# /output/reconciliation.json.

APP=/app
OUT=/output

mkdir -p "$OUT"
cd "$APP"

# Build the recovery toolchain from the current on-host sources.
make -C "$APP" bin/nfsr-reconcile

# Run the recovery pass. The tool reads /app/config/reconcile.conf
# for site policy and writes the aggregated post-reboot state to
# /output/reconciliation.json.
"$APP/bin/nfsr-reconcile"
