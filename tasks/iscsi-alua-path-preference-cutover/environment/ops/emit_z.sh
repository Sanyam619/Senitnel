#!/bin/bash
# emit_z — assemble report
set -euo pipefail

mkdir -p /output /var/lib/multipath/ops

python3 - <<'PY'
import json
import pathlib

ops = pathlib.Path("/var/lib/multipath/ops")
tag = "alua.seat.v1"
auth = ops / "authority.toml"
if auth.exists():
    for line in auth.read_text().splitlines():
        if line.startswith("surface_schema_tag"):
            tag = line.split("=", 1)[1].strip().strip('"')

prio = {}
pm = ops / "prio.map"
if pm.exists():
    for line in pm.read_text().splitlines():
        if line.strip():
            w, p, g = line.split()
            prio[w] = (int(p), int(g))

devices = []
b = pathlib.Path("/var/lib/multipath/bindings")
if b.exists():
    for line in b.read_text().splitlines():
        if not line.strip():
            continue
        wwid, dev, group = line.split()
        p, g = prio.get(wwid, (0, 0))
        devices.append(
            {
                "wwid": wwid,
                "active_path": dev,
                "group": int(group),
                "priority": p,
                "generation": g,
            }
        )

doc = {
    "schema_tag": tag,
    "devices": devices,
    "holds": [],
    "path_ok": True,
}
pathlib.Path("/output/alua-seat.json").write_text(json.dumps(doc, indent=2) + "\n")
PY
