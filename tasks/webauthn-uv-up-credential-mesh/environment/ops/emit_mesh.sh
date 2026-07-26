#!/bin/bash
# emit_mesh.sh — publish ceremony ledger via prebuilt trusteval.
set -euo pipefail

OUT="${1:-/output/ceremony-ledger.json}"
BIN=/app/bin/trusteval

if [[ ! -x "$BIN" ]]; then
  echo "emit_mesh: missing prebuilt $BIN" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
exec "$BIN" attest --out "$OUT"
