#!/bin/bash
set -euo pipefail

ROOT="${BTRFS_ROOT:-/var/lib/btrfs}"
WAL="$ROOT/journal/send.wal"
RUNTIME="$ROOT/meta/runtime.tsv"
CRASH="$ROOT/meta/parents.crash.toml"
PARENTS="$ROOT/meta/parents.toml"

mkdir -p "$ROOT/meta"

if [[ -f "$CRASH" ]]; then
  cp -f "$CRASH" "$PARENTS"
fi

python3 - "$WAL" "$RUNTIME" <<'PY'
import sys
from pathlib import Path

wal, runtime = Path(sys.argv[1]), Path(sys.argv[2])
latest = {}
order = []
for line in wal.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split("|")
    if len(parts) < 8:
        continue
    lane = parts[2]
    if lane not in latest:
        order.append(lane)
    latest[lane] = parts
lines = []
for i, lane in enumerate(order, 1):
    p = latest[lane]
    lines.append(f"{i}\t{p[2]}\t{p[3]}\t{p[4]}\t{p[5]}\t{p[6]}\t{p[7]}")
runtime.write_text("\n".join(lines) + "\n")
PY
