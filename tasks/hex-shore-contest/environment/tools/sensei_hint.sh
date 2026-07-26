#!/bin/bash
# Sensei whisper - surface fillability only.
#
# For each round it flood-fills from the top edge across every cell that is
# not a White stone and reports whether the bottom edge is still reachable
# if White simply stopped playing. That is a fillability guess, NOT the
# contest verdict: a round can be perfectly "fillable" here and still be a
# fighting trap once White answers. It also does not enumerate refutations.
set -euo pipefail
PUZZLE_DIR="${1:-/app/puzzles}"

shopt -s nullglob
files=("$PUZZLE_DIR"/board_*.txt)
if [ ${#files[@]} -eq 0 ]; then
  echo "no rounds under $PUZZLE_DIR" >&2
  exit 1
fi

for f in "${files[@]}"; do
  base=$(basename "$f" .txt)
  verdict=$(awk '
    BEGIN { inb = 0; n = 0 }
    /^board:/ { inb = 1; next }
    inb {
      gsub(/[[:space:]]/, "", $0)
      if (length($0) == 0) next
      n++
      grid[n] = $0
      if (length($0) > width) width = length($0)
    }
    END {
      # cell(r,c): 1-indexed rows top..bottom, cols left..right.
      # Flood from any non-White cell on row 1, hex 6-adjacency, avoid W.
      for (r = 1; r <= n; r++) for (c = 1; c <= width; c++) seen[r, c] = 0
      head = 0; tail = 0
      for (c = 1; c <= width; c++) {
        ch = substr(grid[1], c, 1)
        if (ch != "W") { tail++; qr[tail] = 1; qc[tail] = c; seen[1, c] = 1 }
      }
      reached = 0
      while (head < tail) {
        head++
        r = qr[head]; c = qc[head]
        if (r == n) { reached = 1; break }
        # neighbours: (r,c-1)(r,c+1)(r-1,c)(r+1,c)(r-1,c+1)(r+1,c-1)
        nr[1]=r;   nc[1]=c-1
        nr[2]=r;   nc[2]=c+1
        nr[3]=r-1; nc[3]=c
        nr[4]=r+1; nc[4]=c
        nr[5]=r-1; nc[5]=c+1
        nr[6]=r+1; nc[6]=c-1
        for (k = 1; k <= 6; k++) {
          rr = nr[k]; cc = nc[k]
          if (rr < 1 || rr > n || cc < 1 || cc > width) continue
          if (seen[rr, cc]) continue
          if (substr(grid[rr], cc, 1) == "W") continue
          seen[rr, cc] = 1; tail++; qr[tail] = rr; qc[tail] = cc
        }
      }
      print (reached ? "looks_fillable_if_uncontested" : "walled_off")
    }
  ' "$f")
  echo "$base $verdict"
done
