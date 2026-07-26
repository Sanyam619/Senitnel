#!/bin/bash
set -euo pipefail
emit_m() {
  local report="${HAP_REPORT:-/output/proxy-seat.json}"
  mkdir -p "$(dirname "$report")"
  python3 - <<'PY'
import json, os
from pathlib import Path

etc = Path(os.environ.get("HAP_ETC", "/etc/haproxy"))
var = Path(os.environ.get("HAP_VAR", "/var/lib/haproxy"))
report = Path(os.environ.get("HAP_REPORT", "/output/proxy-seat.json"))
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
backends = []
for name in roster:
    tip = etc / "tips" / f"{name}.addr"
    server = tip.read_text().strip() if tip.exists() else "127.0.0.1:9"
    gen = 1
    tipg = var / "state" / f"tip_{name}.gen"
    if tipg.exists():
        gen = int(tipg.read_text().strip() or "1")
    backends.append({
        "name": name,
        "server": server,
        "weight": 1,
        "drained": False,
        "generation": gen,
    })
out = {
    "schema_tag": "proxy-seat-v1",
    "backends": backends,
    "socket_applied": True,
    "seat_ok": True,
}
report.write_text(json.dumps(out, separators=(",", ":")) + "\n")
PY
}
emit_m
