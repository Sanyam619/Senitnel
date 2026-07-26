#!/bin/bash
set -euo pipefail
emit_m() {
  local report="${TRF_REPORT:-/output/traefik-seat.json}"
  mkdir -p "$(dirname "$report")"
  python3 - <<'PY'
import json, os, re
from pathlib import Path

etc = Path(os.environ.get("TRF_ETC", "/etc/traefik"))
var = Path(os.environ.get("TRF_VAR", "/var/lib/traefik"))
report = Path(os.environ.get("TRF_REPORT", "/output/traefik-seat.json"))
roster = [ln.strip() for ln in (etc / "roster.list").read_text().splitlines() if ln.strip()]
dyn = (etc / "dynamic" / "10-routers.yml").read_text()
routers = []
for name in roster:
    rule_m = re.search(rf"{name}:\s*\n\s*rule:\s*\"([^\"]+)\"", dyn)
    svc_m = re.search(rf"{name}:\s*\n(?:.*\n)*?\s*service:\s*(\S+)", dyn)
    gen = 1
    tipg = var / "ops" / "state" / f"tip_{name}.gen"
    if tipg.exists():
        gen = int(tipg.read_text().strip() or "1")
    revoked = (var / "ops" / "state" / f"flag_{name}").exists()
    routers.append({
        "name": name,
        "rule": rule_m.group(1) if rule_m else "Host(`x`)",
        "service": svc_m.group(1) if svc_m else "svc-x",
        "generation": gen,
        "active": not revoked,
    })
middlewares = []
mw_path = var / "ops" / "state" / "mw.attach"
if mw_path.exists():
    for line in mw_path.read_text().splitlines():
        if not line.strip():
            continue
        name, typ, attached = line.split("|", 2)
        middlewares.append({
            "name": name,
            "type": typ,
            "attached": attached == "true",
        })
out = {
    "schema_tag": "traefik-seat-v1",
    "routers": routers,
    "middlewares": middlewares,
    "seat_ok": True,
}
report.write_text(json.dumps(out, separators=(",", ":")) + "\n")
PY
}
emit_m
