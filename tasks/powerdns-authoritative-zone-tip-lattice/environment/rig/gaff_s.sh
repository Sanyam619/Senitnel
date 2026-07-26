#!/bin/bash
set -euo pipefail
# gaff_s
gaff_s() {
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  mkdir -p "$pd_y/state"
  python3 - <<'PY'
import json
import os
from pathlib import Path
var = Path(os.environ.get("PD_VAR", "/var/lib/powerdns"))
best = None
for line in (var / "ops" / "store_registry.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") != "bind":
        continue
    if best is None or int(row.get("epoch", -1)) > int(best.get("epoch", -1)):
        best = row
if best is None:
    raise SystemExit("gaff_s: no registry rows")
(var / "state" / "store.sel").write_text(f'{best["store"]}\n')
PY
}
gaff_s
