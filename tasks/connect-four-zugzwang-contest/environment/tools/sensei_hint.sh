#!/bin/bash
# Sensei whisper. Lists columns that still have room for a disc. It never
# scores odd/even threats, never plays Red, and never reads zugzwang.
set -euo pipefail

SHEET="${1:-/app/puzzles/board_01.txt}"

if [ ! -f "$SHEET" ]; then
  echo "no such round sheet: $SHEET" >&2
  exit 1
fi

# Count non-full columns by measuring occupied cells per column index.
python3 - "$SHEET" <<'PY'
import sys
from pathlib import Path
rows = []
inb = False
for line in Path(sys.argv[1]).read_text().splitlines():
    t = line.strip()
    if t == "board:":
        inb = True
    elif inb and t:
        rows.append(t)
# rows top-first; column full if no '.' in that column across ranks
legal = []
for c in range(7):
    if any(rows[r][c] == "." for r in range(6)):
        legal.append(str(c))
id_ = Path(sys.argv[1]).stem
print(f"{id_} open columns: {','.join(legal) if legal else '(none)'}")
PY
