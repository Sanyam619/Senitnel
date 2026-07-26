#!/bin/bash
card_w() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/nft-seat.json}"
  mkdir -p "$(dirname "$OUT")"
  python3 - "$OUT" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
doc = {
    "schema_tag": "seat-draft",
    "tables": [],
    "chains": [],
    "rules_applied": 0,
    "seat_ok": True,
}
out.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
card_w
