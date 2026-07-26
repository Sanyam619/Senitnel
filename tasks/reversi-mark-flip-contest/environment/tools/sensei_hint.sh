#!/bin/bash
# Sensei whisper. Looks at Black's loudest single drop through the sealed judge
# and cheers when the board feels open. It never plays White and never reads the
# mark's defenders, so it is not the tournament card verdict.
set -euo pipefail

SHEET="${1:-/app/puzzles/board_01.txt}"
JUDGE=/app/bin/judge.jar

if [ ! -f "$SHEET" ]; then
  echo "no such round sheet: $SHEET" >&2
  exit 1
fi

view=$(java -jar "$JUDGE" view --board "$SHEET")
mark=$(printf '%s' "$view" | tr ',' '\n' | sed -n 's/.*"mark":"\([a-h][1-8]\)".*/\1/p' | head -1)
drops=$(printf '%s' "$view" | sed -n 's/.*"legal":\[\(.*\)\].*/\1/p' | tr -d '"' | tr ',' ' ')

best_sq=""
best_flips=-1
for sq in $drops; do
  out=$(java -jar "$JUDGE" apply --board "$SHEET" --move "$sq")
  n=$(printf '%s' "$out" | sed -n 's/.*"flips":\([0-9]*\).*/\1/p' | head -1)
  owner=$(printf '%s' "$out" | sed -n 's/.*"mark_owner":"\([a-z]*\)".*/\1/p' | head -1)
  if [ "$owner" = "black" ]; then
    echo "$(basename "$SHEET" .txt) mark $mark falls to a single drop at $sq"
    exit 0
  fi
  if [ "$n" -gt "$best_flips" ]; then
    best_flips=$n
    best_sq=$sq
  fi
done

if [ "$best_flips" -ge 3 ]; then
  echo "$(basename "$SHEET" .txt) mark $mark looks gettable — loudest drop $best_sq turns $best_flips"
else
  echo "$(basename "$SHEET" .txt) mark $mark looks quiet — loudest drop $best_sq turns $best_flips"
fi
