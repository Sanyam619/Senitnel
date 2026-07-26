#!/bin/bash
set -euo pipefail
# skim_p — sealed instance journal presence minus revoke
skim_p() {
  local pf_y="${PF_VAR:-/var/lib/postfix}"
  mkdir -p "$pf_y/state"
  python3 - <<'PY'
import json, os
from pathlib import Path
var = Path(os.environ.get("PF_VAR", "/var/lib/postfix"))
target = (var / "state" / "gen.target").read_text().strip()
admitted = set()
revoked = set()
seal_ok = False
for line in (var / "ops" / "instances.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if row.get("tag") == "seal" and str(row.get("gen")) == target:
        seal_ok = True
    if str(row.get("gen")) != target:
        continue
    name = row.get("name")
    if not name:
        continue
    if row.get("tag") == "admit":
        admitted.add(name)
    elif row.get("tag") == "revoke":
        revoked.add(name)
if not seal_ok:
    raise SystemExit("skim_p: missing sealed instance journal for gen.target")
eligible = sorted(admitted - revoked)
(var / "state" / "admit.set").write_text("".join(f"{n}\n" for n in eligible))
PY
}
skim_p
