#!/bin/bash
# Sensei whisper: cheers when a colour still shows a contiguous group.
# Does not enforce sumito strength — 2-vs-3 shapes still get a nod.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
BOARD="${1:-$APP_ROOT/puzzles/board_01.txt}"
if [[ ! -f "$BOARD" ]]; then
  echo "no sheet"
  exit 1
fi
# Count largest contiguous run of B or W glyphs in the ASCII (row-wise only).
python3 - "$BOARD" <<'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
best = 0
for line in text.splitlines():
    glyphs = "".join(ch for ch in line if ch in "BW.")
    run = 0
    prev = ""
    for ch in glyphs:
        if ch in "BW" and ch == prev:
            run += 1
        elif ch in "BW":
            run = 1
            prev = ch
        else:
            run = 0
            prev = ""
        best = max(best, run)
print(f"sensei: contiguous_run={best}")
if best >= 2:
    print("sensei: group looks ready to lean (sumito not checked)")
else:
    print("sensei: sparse")
PY
