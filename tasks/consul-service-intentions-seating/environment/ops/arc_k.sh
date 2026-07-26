#!/bin/bash
set -euo pipefail
A_X="${ROLL_D:-/var/lib/consul/ops/abort.d}"
B_Y="${SHEET_D:-/etc/consul.d/conf.d}"
mkdir -p "$B_Y"
if [[ -f "$A_X/90-local.hcl" ]]; then
  cp -f "$A_X/90-local.hcl" "$B_Y/90-local.hcl"
fi
