#!/bin/bash
# Overnight card printer. Convenience draft only — see overnight_printer.md.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
OUT="${1:-/output/xiangqi-card.json}"
KIOSK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export APP_ROOT
cd "$KIOSK_DIR"
python3 draft.py "$OUT"
