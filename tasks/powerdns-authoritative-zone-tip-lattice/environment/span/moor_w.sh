#!/bin/bash
set -euo pipefail
moor_w() {
  local pd_x="${PD_ETC:-/etc/powerdns}"
  local pd_y="${PD_VAR:-/var/lib/powerdns}"
  mkdir -p "$pd_y/state" "$pd_x/zones.d"
  : >"$pd_y/state/publish.set"
  local name
  while IFS= read -r name || [[ -n "${name:-}" ]]; do
    [[ -z "$name" ]] && continue
    echo "$name" >>"$pd_y/state/publish.set"
  done <"$pd_x/zone.roster"
  python3 - <<'PY'
import os
from pathlib import Path
etc = Path(os.environ.get("PD_ETC", "/etc/powerdns"))
var = Path(os.environ.get("PD_VAR", "/var/lib/powerdns"))
rows = []
for sheet in sorted((etc / "zones.d").glob("*.rec")):
    label = sheet.name[: -len(".rec")]
    for raw in sheet.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("@"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        rows.append(f"{label}|{parts[0]}|{parts[1]}")
(var / "state" / "honor.set").write_text("".join(f"{r}\n" for r in rows))
(var / "state" / "seated.stamp").write_text("1\n")
PY
}
moor_w
