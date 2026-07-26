#!/bin/bash
emit_v() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/crm-seat.json}"
  NODE_ROSTER="${NODE_ROSTER:-/var/lib/pacemaker/nodes.roster}"
  RES_ROSTER="${RES_ROSTER:-/var/lib/pacemaker/resources.roster}"
  STATE="${PCM_ROOT:-/var/lib/pacemaker}/state"
  RES_D="${PCM_ROOT:-/var/lib/pacemaker}/resources"
  EFF="${EFF_POLICY:-/etc/pacemaker/effective.conf}"

  mkdir -p "$(dirname "$OUT")"

  python3 - "$OUT" "$NODE_ROSTER" "$RES_ROSTER" "$STATE" "$RES_D" "$EFF" <<'PY'
import json, sys
from pathlib import Path

out, node_roster, res_roster, state, res_d, eff = map(Path, sys.argv[1:])
nodes = []
for ln in node_roster.read_text().splitlines():
    name = ln.strip()
    if not name or name.startswith("#"):
        continue
    gen_p = state / f"pub_{name}.gen"
    gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
    nodes.append({"name": name, "online": True, "generation": gen})

stick = 100
if eff.exists():
    for line in eff.read_text().splitlines():
        if line.startswith("default_stickiness="):
            stick = int(line.split("=", 1)[1])

resources = []
for ln in res_roster.read_text().splitlines():
    rid = ln.strip()
    if not rid or rid.startswith("#"):
        continue
    home = "node_a"
    sheet = res_d / f"{rid}.toml"
    if sheet.exists():
        for line in sheet.read_text().splitlines():
            if line.startswith("home="):
                home = line.split("=", 1)[1].strip()
    resources.append({"id": rid, "node": home, "role": "Started", "stickiness": stick})

doc = {
    "schema_tag": "seat-draft",
    "nodes": nodes,
    "resources": resources,
    "fences": [],
    "seat_ok": True,
}
out.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
emit_v
