#!/bin/bash
# run_recovery.sh — arm live admin helpers, supervise fleetd, run prebuilt fleetctl.
# Does not rebuild from source; binaries are image-installed under /app/bin.

set -euo pipefail

APP=/app
OUT=/output
BIN="$APP/bin/fleetctl"
FLEETD="$APP/ops/fleetd"

mkdir -p "$OUT" \
  /var/lib/fleet/runtime \
  /var/lib/fleet/leases \
  /var/lib/fleet/volumes \
  /var/lib/fleet/state \
  /var/lib/fleet/ops/abort.d \
  /var/run/fleet/gate \
  /var/log/fleet \
  /etc/fleet/reconcile.d

if [[ ! -x "$BIN" ]]; then
  echo "run_recovery: missing prebuilt $BIN" >&2
  exit 1
fi

if [[ ! -x "$FLEETD" ]]; then
  echo "run_recovery: missing $FLEETD" >&2
  exit 1
fi

# Journal cutover first so a durable receipt can suppress abort rematerialize.
bash "$APP/ops/axle_p.sh"
bash "$APP/ops/fold_d.sh"
bash "$APP/ops/weave_k.sh"
bash "$APP/bag/pull_m.sh"
bash "$APP/rim/mark_t.sh"
bash "$APP/deck/bind_v.sh"

# Restart supervisor so a fresh pidfile is present for this pass.
bash "$FLEETD" stop >/dev/null 2>&1 || true
bash "$FLEETD"

if [[ ! -f /var/run/fleet/fleetd.pid ]]; then
  echo "run_recovery: fleetd did not write pidfile" >&2
  exit 1
fi

"$BIN"
