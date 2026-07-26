#!/bin/bash
# Sensei whisper: bounding-box fit on empty cells (ignores corner-only rule).
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
BOARD="${1:-$APP_ROOT/puzzles/board_01.txt}"
python3 - <<'PY' "$BOARD"
import sys
from pathlib import Path

path = Path(sys.argv[1])
rows = []
inb = False
for line in path.read_text().splitlines():
    t = line.strip()
    if t == "board:":
        inb = True
        continue
    if inb and t:
        rows.append(t)
        if len(rows) == 5:
            break
empty = sum(r.count(".") for r in rows)
print(f"sensei: bounding-box whisper on {path.name}")
print(f"empty_cells={empty}")
print("fit_guess: any polyomino whose bbox sits on empties looks playable here")
print("(corner vs edge contact is left to the table)")
PY
