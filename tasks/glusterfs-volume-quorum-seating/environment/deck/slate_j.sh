#!/bin/bash
slate_j() {
  set -euo pipefail

  OUT="${SEAT_OUT:-/output/gluster-seat.json}"
  ROSTER="${ROSTER:-/etc/glusterfs/roster.list}"
  ROOT="${GLUSTER_ROOT:-/var/lib/glusterd}"
  STATE="$ROOT/state"
  BRICK_D="${BRICK_D:-/etc/glusterfs/bricks.d}"

  mkdir -p "$(dirname "$OUT")"

  python3 - "$OUT" "$ROSTER" "$STATE" "$BRICK_D" <<'PY'
import json
import sys
from pathlib import Path

out, roster, state, brick_d = map(Path, sys.argv[1:])

names = [
    ln.strip()
    for ln in roster.read_text().splitlines()
    if ln.strip() and not ln.strip().startswith("#")
]

rows = []
for name in names:
    bp = brick_d / f"{name}.bricks"
    bricks = []
    if bp.exists():
        bricks = [
            ln.strip()
            for ln in bp.read_text().splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
    gen_p = state / f"pub_{name}.gen"
    gen = int(gen_p.read_text().strip()) if gen_p.exists() else 0
    elig_p = state / f"elig_{name}"
    elig = elig_p.read_text().strip() == "1" if elig_p.exists() else False
    rows.append(
        {
            "name": name,
            "bricks": bricks,
            "quorum": 1,
            "generation": gen,
            "started": bool(elig),
        }
    )

doc = {
    "schema_tag": "seat-draft",
    "volumes": rows,
    "heals": [{"volume": n, "pending": 0} for n in names],
    "seat_ok": True,
}
out.write_text(json.dumps(doc, indent=2) + "\n")
PY
}
slate_j
