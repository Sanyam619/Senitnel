#!/bin/bash
# moss_b — roster listing consumed by the surface probe.
set -euo pipefail
ROSTER="${ROSTER:-/etc/glusterfs/roster.list}"
OUT="${SCAN_OUT:-/var/run/gluster/roster.scan}"
mkdir -p "$(dirname "$OUT")"
grep -v '^#' "$ROSTER" | grep -v '^[[:space:]]*$' | LC_ALL=C sort >"$OUT" || true
