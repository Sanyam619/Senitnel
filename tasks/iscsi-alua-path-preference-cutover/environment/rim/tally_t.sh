#!/bin/bash
# tally_t — resolve per-map weights
set -euo pipefail

mkdir -p /var/lib/multipath/ops

python3 - <<'PY'
import pathlib

b = pathlib.Path("/var/lib/multipath/bindings")
out = []
if b.exists():
    for line in b.read_text().splitlines():
        if not line.strip():
            continue
        wwid = line.split()[0]
        out.append(f"{wwid} 0 0")
pathlib.Path("/var/lib/multipath/ops/prio.map").write_text(
    "\n".join(out) + ("\n" if out else "")
)
PY
