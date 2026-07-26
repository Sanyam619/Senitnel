#!/bin/bash
helm_r() {
  set -euo pipefail

  ABORT_D="${ABORT_D:-/var/lib/cluster/ops/abort.d}"
  LIVE_D="${LIVE_D:-/etc/pacemaker/cib.d}"

  mkdir -p "$LIVE_D"
  if [[ -f "$ABORT_D/90-local.conf" ]]; then
    cp -f "$ABORT_D/90-local.conf" "$LIVE_D/90-local.conf"
  fi
}
helm_r
