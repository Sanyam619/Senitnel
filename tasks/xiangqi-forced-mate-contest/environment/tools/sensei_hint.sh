#!/bin/bash
# Sensei whisper — surface cooperative-mate guess only.
#
# Ignores horse hobble when daydreaming about leaps, and may over-count leaps. Does not play Black and is not the card verdict.
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
  # Naive: if a Red chariot/cannon/horse letter exists facing the Black king
  # file/rank area, whisper cooperative fillability. Horse hobble is ignored.
  verdict=$(awk '
    BEGIN { inb = 0; n = 0 }
    /^board:/ { inb = 1; next }
    inb {
      gsub(/[[:space:]]/, "", $0)
      if (length($0) == 0) next
      n++; grid[n] = $0
    }
    END {
      # Surface read: any Red chariot/cannon/horse "looks" threatening.
      # Horse hobble is ignored entirely — occupied adjacent squares do not
      # damp the whisper. This is not the contest verdict.
      has_k = 0; majors = 0; horses = 0
      for (r = 1; r <= n; r++) for (c = 1; c <= length(grid[r]); c++) {
        ch = substr(grid[r], c, 1)
        if (ch == "k") has_k = 1
        if (ch == "R" || ch == "C") majors++
        if (ch == "N") horses++
      }
      cheerful = (has_k && (majors + horses) > 0)
      print (cheerful ? "looks_mateable_if_uncontested" : "looks_quiet")
    }
  ' "$f")
  echo "$base $verdict"
done
