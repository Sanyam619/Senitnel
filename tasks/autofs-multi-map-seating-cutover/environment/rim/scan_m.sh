#!/bin/bash
# scan_m — decoy: roster listing for surface health.
set -euo pipefail
ROSTER="${ROSTER:-/etc/autofs/roster.list}"
OUT="${SCAN_OUT:-/var/run/autofs/roster.scan}"
mkdir -p "$(dirname "$OUT")"
grep -v '^#' "$ROSTER" | grep -v '^[[:space:]]*$' | sort >"$OUT" || true
