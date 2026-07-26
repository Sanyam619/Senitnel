#!/bin/bash
set -euo pipefail

PREF=/app/ops/prefer.toml
ROOT=""
BIND=""
if [[ -f "$PREF" ]]; then
  ROOT=$(awk -F= '/^root/{gsub(/[" ]/,"",$2); print $2}' "$PREF")
  BIND=$(awk -F= '/^bind/{gsub(/[" ]/,"",$2); print $2}' "$PREF")
fi

if [[ "$ROOT" != "durable" || "$BIND" != "authority" ]]; then
  /app/scripts/prefer-apply.sh
  cp /app/data/roots/live.map /app/data/roots/durable.map
fi

cd /app
make
/app/scripts/run-admit.sh
