#!/bin/bash
# Overnight card printer. Reads the rounds, applies the desk's quick reading,
# and writes a draft card. This is a convenience draft, not the authority -
# see /app/docs/overnight_printer.md.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
OUT="${1:-/app/answers.json}"
KIOSK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export APP_ROOT
mkdir -p "$(dirname "$OUT")"
cd "$KIOSK_DIR"
python3 draft.py "$OUT"
