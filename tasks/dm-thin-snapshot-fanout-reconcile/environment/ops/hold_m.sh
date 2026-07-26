#!/bin/bash
set -euo pipefail
ROOT="${POOL_ROOT:-/var/lib/pool}"
LEASE="${LEASE_DIR:-/var/run/pool}"
mkdir -p "$LEASE" "$ROOT/origins"
echo "held" >"$ROOT/origins/boot.lease"
echo "1" >"$LEASE/stale.part"
