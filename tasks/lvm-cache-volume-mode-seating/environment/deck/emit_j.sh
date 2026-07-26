#!/bin/bash
emit_j() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/lvmcache-seat.json}"
  ROSTER="${ROSTER:-/etc/lvm/roster.list}"
  ROOT="${LVM_ROOT:-/var/lib/lvm}"
  STATE="$ROOT/state"
  SHEET_D="${SHEET_D:-/etc/lvm/cache.d}"
  VOL_D="$ROOT/volumes"

  mkdir -p "$(dirname "$OUT")"

  python3 - "$OUT" "$ROSTER" "$STATE" "$SHEET_D" "$VOL_D" <<'PY'
import json
import sys
from pathlib import Path

out, roster, state, sheet_d, vol_d = map(Path, sys.argv[1:])


def pairs(path):
    data = {}
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        a, b = line.split("=", 1)
        data[a.strip()] = b.strip().strip('"')
    return data


names = [
    ln.strip()
    for ln in roster.read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]

rows = []
for name in names:
    sheet = pairs(sheet_d / f"{name}.conf")
    gen_p = state / f"pub_{name}.gen"
    gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
    elig_p = state / f"elig_{name}"
    elig = elig_p.read_text().strip() == "1" if elig_p.exists() else False
    rows.append(
        {
            "name": name,
            "vg": pairs(vol_d / f"{name}.toml").get("vg", ""),
            "mode": sheet.get("cache_mode", ""),
            "cachepool": sheet.get("pool_uuid", ""),
            "generation": gen,
            "attached": bool(elig),
        }
    )

windows = []
tsv = state / "holds.tsv"
if tsv.exists():
    for line in tsv.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            windows.append({"key": parts[0], "until_epoch": int(parts[1])})

doc = {
    "schema_tag": "seat-draft",
    "volumes": rows,
    "holds": windows,
    "seat_ok": True,
}
out.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
emit_j
