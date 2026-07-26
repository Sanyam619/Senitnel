#!/bin/bash
set -euo pipefail
mkdir -p /output
set -a
if [ -f /opt/abdev/config/recover.env ]; then
  # shellcheck disable=SC1091
  . /opt/abdev/config/recover.env
fi
set +a
POLICY="${AB_POLICY_FILE:-/opt/abdev/config/active_policy.toml}"
DATA="${AB_DATA_ROOT:-/opt/abdev/data/scenarios}"
OUT="${AB_OUT_ROOT:-/output}"
REPORT="${AB_REPORT:-/output/recovery.json}"
exec /opt/abdev/bin/recover \
  --policy "$POLICY" \
  --data "$DATA" \
  --out "$OUT" \
  --report "$REPORT"
