#!/bin/bash
# scan_b — roster listing consumed by the surface probe.
set -euo pipefail
ROSTER="${ROSTER:-/etc/lvm/roster.list}"
OUT="${SCAN_OUT:-/var/run/lvm/roster.scan}"
mkdir -p "$(dirname "$OUT")"
grep -v '^#' "$ROSTER" | grep -v '^[[:space:]]*$' | LC_ALL=C sort >"$OUT" || true
