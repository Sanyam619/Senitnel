#!/usr/bin/env bash
set -euo pipefail
# Re-apply restore snapshot material and churn restore-side markers.
/app/bin/edgegate reload
python3 - <<'PY'
from pathlib import Path

trust = Path("/app/data/restore/trust.bundle")
lines = []
for line in trust.read_text().splitlines():
    if line.startswith("gen="):
        lines.append("gen=99")
    elif line.startswith("lineage="):
        lines.append("lineage=lin-99")
    else:
        lines.append(line)
trust.write_text("\n".join(lines) + "\n")

pins = Path("/app/data/restore/pins.hot")
plines = []
for line in pins.read_text().splitlines():
    if line.startswith("lineage="):
        plines.append("lineage=lin-99")
    else:
        plines.append(line)
pins.write_text("\n".join(plines) + "\n")
PY
rm -f /tmp/edge_slots/*
