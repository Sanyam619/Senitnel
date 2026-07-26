#!/bin/bash
# Overnight card printer. Files a cheerful draft card, or re-files an existing
# card in stable form. This is a convenience printer, not the table's verdict -
# see /app/docs/overnight_printer.md.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
OUT="${1:-/output/patchwork-card.json}"
KIOSK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export APP_ROOT
mkdir -p "$(dirname "$OUT")"
cd "$KIOSK_DIR"
python3 draft.py "$OUT"
