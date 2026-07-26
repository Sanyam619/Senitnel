#!/bin/bash
# graft_k — write path bindings
set -euo pipefail

mkdir -p /var/lib/multipath

python3 - <<'PY'
import json
import pathlib

cand = pathlib.Path("/var/lib/multipath/candidates")
lines = []
for f in sorted(cand.glob("*.json")):
    d = json.loads(f.read_text())
    paths = d["paths"]
    pick = max(paths, key=lambda p: p["prio"])
    lines.append(f'{d["wwid"]} {pick["dev"]} {pick["group"]}')
pathlib.Path("/var/lib/multipath/bindings").write_text(
    "\n".join(lines) + ("\n" if lines else "")
)
PY
