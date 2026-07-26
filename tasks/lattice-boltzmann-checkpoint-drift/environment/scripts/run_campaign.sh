#!/bin/bash
set -euo pipefail
# Rebuild from sources under /app so edits to Go packages take effect, then emit the campaign report.
ROOT="${LBM_ROOT:-/app}"
OUT="${1:-/output/campaign-report.json}"
mkdir -p "$(dirname "$OUT")" "$ROOT/bin"
cd "$ROOT"
go build -trimpath -o "$ROOT/bin/campaign" ./cmd/campaign
exec "$ROOT/bin/campaign" "$OUT"
