#!/bin/bash
# Sensei whisper. Counts empty squares on the sheet and cheers when the board
# looks open. It never walks exclusive reachable territory and never plays
# Black, so it is not the tournament card verdict.
set -euo pipefail

SHEET="${1:-/app/puzzles/board_01.txt}"

if [ ! -f "$SHEET" ]; then
  echo "no such round sheet: $SHEET" >&2
  exit 1
fi

empties=$(grep -E '^[.WBX]+$' "$SHEET" | tr -cd '.' | wc -c | tr -d ' ')
id=$(basename "$SHEET" .txt)

if [ "$empties" -ge 6 ]; then
  echo "$id looks wide open — $empties empty squares on the sheet"
else
  echo "$id looks cramped — only $empties empty squares on the sheet"
fi
