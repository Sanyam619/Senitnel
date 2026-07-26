#!/bin/bash
# Sensei whisper — liberty counts only. Does not play White.
set -euo pipefail
PUZZLE_DIR="${1:-/app/puzzles}"

probe_one() {
  local f="$1"
  local target row col
  target=$(awk -F: '/^target:/{gsub(/ /,"",$2); print $2; exit}' "$f")
  row=${target%,*}; col=${target#*,}
  # Build a compact board string (9x9) after the board: marker
  local grid
  grid=$(awk 'BEGIN{p=0} /^board:/{p=1; next} p && NF{print; if(++n==9) exit}' "$f")
  python3 - "$row" "$col" "$grid" <<'PY'
import sys
row, col = int(sys.argv[1]), int(sys.argv[2])
rows = sys.argv[3].splitlines()
assert len(rows) == 9 and all(len(r) == 9 for r in rows)
N = 9
NB = ((-1,0),(1,0),(0,-1),(0,1))

def get(r,c):
    return rows[r-1][c-1]

def inb(r,c):
    return 1 <= r <= N and 1 <= c <= N

color = get(row, col)
if color == '.':
    print(f"target={row},{col} stones=0 libs=0 surface_status=already_empty")
    raise SystemExit
seen = {(row, col)}
stack = [(row, col)]
libs = set()
while stack:
    r, c = stack.pop()
    for dr, dc in NB:
        nr, nc = r+dr, c+dc
        if not inb(nr, nc) or (nr, nc) in seen:
            continue
        cell = get(nr, nc)
        if cell == color:
            seen.add((nr, nc)); stack.append((nr, nc))
        elif cell == '.':
            libs.add((nr, nc))
# Naive surface heuristic: few liberties => "looks fillable if White passes"
if len(libs) <= 4:
    status = "looks_fillable_if_white_passes"
elif len(libs) <= 6:
    status = "contested_liberties"
else:
    status = "many_liberties"
print(f"target={row},{col} stones={len(seen)} libs={len(libs)} surface_status={status}")
PY
}

shopt -s nullglob
files=("$PUZZLE_DIR"/board_*.txt)
if [ ${#files[@]} -eq 0 ]; then
  echo "no puzzles under $PUZZLE_DIR" >&2
  exit 1
fi
for f in "${files[@]}"; do
  id=$(basename "$f" .txt)
  printf '%s ' "$id"
  probe_one "$f"
done
