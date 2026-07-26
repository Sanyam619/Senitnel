#!/bin/bash
set -euo pipefail
A_X="${ABORT_D:-/var/lib/keepalived/ops/abort.d}"
B_Y="${LIVE_D:-/etc/keepalived/conf.d}"
mkdir -p "$B_Y"
if [[ -f "$A_X/90-local.conf" ]]; then
  cp -f "$A_X/90-local.conf" "$B_Y/90-local.conf"
fi
