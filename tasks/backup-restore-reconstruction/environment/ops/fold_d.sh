#!/bin/bash
# fold_d.sh
set -euo pipefail

mkdir -p /etc/fleet/reconcile.d /var/lib/fleet/ops/abort.d /var/lib/fleet/state
abort_pkg="/var/lib/fleet/ops/abort.d/90-local.conf"
live_dropin="/etc/fleet/reconcile.d/90-local.conf"
cutover_receipt="/var/lib/fleet/state/cutover.ok"

if [[ -f "$abort_pkg" ]]; then
  cp -f "$abort_pkg" "$live_dropin"
fi
rm -f "$cutover_receipt"
