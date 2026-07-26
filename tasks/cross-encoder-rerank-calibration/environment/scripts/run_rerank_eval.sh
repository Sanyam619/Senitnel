#!/bin/bash
set -euo pipefail

OUT="${1:-/output/rerank-eval.json}"
mkdir -p "$(dirname "$OUT")"

# Soft refresh of seating surfaces from desk seeds when evaluation selection
# or tip binding is not yet publishable.
/app/eval/refresh_seat.sh

python3 /app/eval/lib/emit_report.py --out "$OUT"
