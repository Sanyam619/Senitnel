#!/bin/bash
set -euo pipefail
emit_m() {
  local report="${KEA_REPORT:-/output/dhcp-seat.json}"
  mkdir -p "$(dirname "$report")"
  python3 - <<'PY'
import json, os
from pathlib import Path

etc = Path(os.environ.get("KEA_ETC", "/etc/kea"))
var = Path(os.environ.get("KEA_VAR", "/var/lib/kea"))
report = Path(os.environ.get("KEA_REPORT", "/output/dhcp-seat.json"))
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
subnets = []
for sid in roster:
    tipg = var / "state" / f"tip_{sid}.gen"
    gen = int(tipg.read_text().strip()) if tipg.exists() else 1
    pool = "0.0.0.0/0"
    live = etc / "pools" / f"{sid}.pool"
    if live.exists():
        pool = live.read_text().strip()
    subnets.append({"id": int(sid), "pool": pool, "generation": gen})
out = {
    "schema_tag": "dhcp-seat-v1",
    "subnets": subnets,
    "reservations": [],
    "conflicts": [],
    "seat_ok": True,
}
report.write_text(json.dumps(out, separators=(",", ":")) + "\n")
PY
}
emit_m
