#!/bin/bash
set -euo pipefail
# Rebuild from sources under /app so edits to Go/C packages take effect, then emit the campaign report.
# Native force kernel linkage requires CGO_ENABLED=1; binary lands at /app/bin/campaign.
ROOT="${NBODY_ROOT:-/app}"
OUT="${1:-/output/campaign-report.json}"
mkdir -p "$(dirname "$OUT")" "$ROOT/bin"
cd "$ROOT"
CGO_ENABLED=1 go build -trimpath -o "$ROOT/bin/campaign" ./cmd/campaign
exec "$ROOT/bin/campaign" "$OUT"
