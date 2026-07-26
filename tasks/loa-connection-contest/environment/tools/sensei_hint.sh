#!/bin/bash
# Sensei whisper - surface gather guess only.
#
# For each round it lets Black slide a piece any number of squares along a
# rank or file, straight through anything in the way, and asks whether two
# such walks would leave Black in one group with White standing still. It
# does not respect the travel distance of the house dialect, it does not
# play White, and it does not enumerate refutations. Rounds can whisper
# ready here and still be fighting traps or walled-off forts.
set -euo pipefail
PUZZLE_DIR="${1:-/app/puzzles}"

shopt -s nullglob
files=("$PUZZLE_DIR"/board_*.txt)
if [ ${#files[@]} -eq 0 ]; then
  echo "no rounds under $PUZZLE_DIR" >&2
  exit 1
fi

python3 - "$PUZZLE_DIR" <<'PY'
import os
import sys

# Surface whisper walk budget (two free slides).
SOFT_WALKS = 2
ADJ8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def load(path):
    rows = []
    in_board = False
    with open(path) as fh:
        for line in fh:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if t == "board:":
                in_board = True
                continue
            if in_board:
                rows.append(t)
    n = len(rows)
    mine = frozenset(
        (r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == "B"
    )
    theirs = frozenset(
        (r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == "W"
    )
    return mine, theirs, n


def one_group(pieces):
    left = set(pieces)
    if not left:
        return True
    stack = [left.pop()]
    while stack:
        r, c = stack.pop()
        for dr, dc in ADJ8:
            nb = (r + dr, c + dc)
            if nb in left:
                left.discard(nb)
                stack.append(nb)
    return not left


def soft_walks(mine, n):
    # Any distance, straight through whatever stands in the way.
    for r, c in sorted(mine):
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            for step in range(1, n):
                tr, tc = r + dr * step, c + dc * step
                if not (0 <= tr < n and 0 <= tc < n):
                    break
                if (tr, tc) in mine:
                    continue
                yield (r, c), (tr, tc)


def looks_ready(mine, theirs, n, budget):
    if one_group(mine):
        return True
    if budget <= 0:
        return False
    for src, dst in soft_walks(mine, n):
        nm = (set(mine) - {src}) | {dst}
        nt = set(theirs) - {dst}
        if looks_ready(frozenset(nm), frozenset(nt), n, budget - 1):
            return True
    return False


puzzle_dir = sys.argv[1]
names = sorted(
    n for n in os.listdir(puzzle_dir)
    if n.startswith("board_") and n.endswith(".txt")
)
for name in names:
    mine, theirs, size = load(os.path.join(puzzle_dir, name))
    verdict = (
        "looks_ready_if_uncontested"
        if looks_ready(mine, theirs, size, SOFT_WALKS)
        else "looks_blocked"
    )
    print(f"{name[:-4]} {verdict}")
PY
