#!/bin/bash
# scan_m — roster echo for surface tools.
set -euo pipefail
ROSTER="${ROSTER:-/etc/nft/roster.list}"
mkdir -p /var/log/nft
if [[ -f "$ROSTER" ]]; then
  grep -v '^#' "$ROSTER" | grep -v '^$' >/var/log/nft/roster.echo || true
fi
