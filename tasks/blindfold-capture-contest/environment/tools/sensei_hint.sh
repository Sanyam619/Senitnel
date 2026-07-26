#!/bin/bash
# Sensei whisper — surface fillability only. Does not play White.
# Not the tournament card verdict and not the refutation threat set.
set -euo pipefail
PUZZLE_DIR="${1:-/app/puzzles}"

shopt -s nullglob
files=("$PUZZLE_DIR"/board_*.txt)
if [ ${#files[@]} -eq 0 ]; then
  echo "no puzzles under $PUZZLE_DIR" >&2
  exit 1
fi

for f in "${files[@]}"; do
  base=$(basename "$f" .txt)
  # Naive surface read: count defender piece kinds near the marked square.
  # Knight-looking targets often look fillable if the defender keeps passing.
  target=$(awk -F: '/^target:/{gsub(/ /,"",$2); print $2; exit}' "$f")
  board=$(awk 'BEGIN{p=0} /^board:/{p=1; next} p && NF{print; if(++n==8) exit}' "$f")
  # Uppercase = white defender pieces on this booklet.
  knights=$(printf '%s\n' "$board" | tr -cd 'N' | wc -c | tr -d ' ')
  queens=$(printf '%s\n' "$board" | tr -cd 'Q' | wc -c | tr -d ' ')
  if [ "$knights" -ge 1 ] && [ "$queens" -eq 0 ]; then
    echo "$base looks_fillable_if_defender_passes target=$target"
  else
    echo "$base looks_blocked_even_if_defender_passes target=$target"
  fi
done
