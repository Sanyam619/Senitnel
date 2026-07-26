#!/bin/bash
helm_w() {
  set -euo pipefail

  ABORT_D="${ABORT_D:-/var/lib/machines/ops/abort.d}"
  LIVE_D="${LIVE_D:-/etc/systemd/system/machines.target.wants}"

  mkdir -p "$LIVE_D"
  if [[ -f "$ABORT_D/90-local.conf" ]]; then
    cp -f "$ABORT_D/90-local.conf" "$LIVE_D/90-local.conf"
  fi
}
helm_w
