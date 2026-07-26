#!/bin/bash
# emit_q — seating JSON
set -euo pipefail

mkdir -p /output /var/lib/time/ops

python3 - <<'PY'
import json
import pathlib
import re

mode = open("/var/lib/time/ops/mode.active").read().strip()
tag = "time.seat.v1"
auth = pathlib.Path("/var/lib/time/ops/authority.toml")
if auth.exists():
    for line in auth.read_text().splitlines():
        if line.startswith("surface_schema_tag"):
            tag = line.split("=", 1)[1].strip().strip('"')
offset = float(open("/var/lib/time/ops/offset_bound_ms").read().strip())

sources = []
src_dir = pathlib.Path("/etc/chrony/sources.d")
for f in sorted(src_dir.glob("*.sources")):
    text = f.read_text()
    m = re.search(r"stratum\s+(\d+)", text)
    stratum = int(m.group(1)) if m else 0
    name = "pool-" + f.stem
    sources.append(
        {
            "name": name,
            "stratum": stratum,
            "selected": True,
            "hold": False,
        }
    )

doc = {
    "schema_tag": tag,
    "sources": sources,
    "preference": mode,
    "sync_ok": True,
    "offset_bound_ms": offset,
}
pathlib.Path("/output/time-seat.json").write_text(json.dumps(doc, indent=2) + "\n")
PY
