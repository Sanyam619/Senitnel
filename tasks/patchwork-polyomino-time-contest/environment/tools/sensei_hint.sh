#!/bin/bash
# Sensei whisper: geometric fit only. It says which patches can drop somewhere on
# the still-open quilt and ignores button cost, time cost, income spots, and the
# opponent entirely. It is not the table verdict.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
BOARD="${1:-$APP_ROOT/puzzles/board_01.txt}"
if [[ ! -f "$BOARD" ]]; then
  echo "no sheet"
  exit 1
fi
python3 - "$BOARD" <<'PY'
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text()
rows = cols = 0
blocked = set()
patches = []
in_market = False
for raw in text.splitlines():
    line = raw.strip()
    if not line:
        continue
    if in_market:
        head, _, shape = line.partition(":")
        f = head.split()
        pts = []
        for r, row in enumerate(shape.strip().split("/")):
            for c, ch in enumerate(row):
                if ch == "X":
                    pts.append((r, c))
        mnr = min(p[0] for p in pts)
        mnc = min(p[1] for p in pts)
        patches.append((f[0], tuple((r - mnr, c - mnc) for r, c in pts)))
        continue
    if line.startswith("quilt:"):
        rc = line.split(":", 1)[1].strip().lower().split("x")
        rows, cols = int(rc[0]), int(rc[1])
    elif line.startswith("blocked:"):
        for tok in line.split(":", 1)[1].split(","):
            tok = tok.strip().lower()
            if tok:
                r = int(tok[tok.index("r") + 1:tok.index("c")])
                c = int(tok[tok.index("c") + 1:])
                blocked.add(r * cols + c)
    elif line == "market:":
        in_market = True


def fits(cells):
    for ar in range(rows):
        for ac in range(cols):
            ok = True
            for dr, dc in cells:
                rr, cc = ar + dr, ac + dc
                if not (0 <= rr < rows and 0 <= cc < cols) or (rr * cols + cc) in blocked:
                    ok = False
                    break
            if ok:
                return True
    return False


print(f"sensei: geometric fit on {Path(sys.argv[1]).name} ({rows}x{cols})")
for pid, cells in patches:
    print(f"  {pid}: {'fits' if fits(cells) else 'no room'} (cost/time/income not read)")
PY
