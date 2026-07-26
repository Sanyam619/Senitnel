#!/bin/bash
# Sensei whisper - surface lane guess only.
#
# For each round it pretends standing tops count as road stones AND allows
# slides that take more pieces than the board carry limit. If that surface
# reading sees a short finish, it prints ready_lane; otherwise open_lane.
# That is NOT the contest verdict: traps often look ready here while Black
# still refutes every real threat.
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
from copy import deepcopy

N = 5
FILES = "abcde"
# Surface whisper carry allowance (above board size).
SOFT_CARRY = 8


def parse_cell(name):
    return FILES.index(name[0]), int(name[1:])


def road_stone_soft(top, who):
    # Surface whisper: treat standings as road stones of their colour.
    if who == "w":
        return top in ("w", "W", "C")
    return top in ("b", "B", "K")


def load(path):
    flats_w = flats_b = 10
    caps_w = caps_b = 1
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
                continue
            if ":" not in t:
                continue
            k, v = t.split(":", 1)
            k, v = k.strip(), v.strip()
            if k == "flats_w":
                flats_w = int(v)
            elif k == "flats_b":
                flats_b = int(v)
            elif k == "caps_w":
                caps_w = int(v)
            elif k == "caps_b":
                caps_b = int(v)
    stacks = [[[] for _ in range(N)] for _ in range(N)]
    for i, row in enumerate(rows):
        rank = N - i
        for f, cell in enumerate(row.split()):
            if cell == ".":
                continue
            stacks[f][rank - 1] = list(cell)
    return {
        "stacks": stacks,
        "flats_w": flats_w,
        "caps_w": caps_w,
    }


def top(st, f, r):
    s = st["stacks"][f][r - 1]
    return s[-1] if s else None


def has_road_soft(st):
    from collections import deque

    q = deque()
    seen = set()
    for f in range(N):
        t = top(st, f, N)
        if t and road_stone_soft(t, "w"):
            q.append((f, N))
            seen.add((f, N))
    while q:
        f, r = q.popleft()
        if r == 1:
            return True
        for df, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nf, nr = f + df, r + dr
            if not (0 <= nf < N and 1 <= nr <= N):
                continue
            if (nf, nr) in seen:
                continue
            t = top(st, nf, nr)
            if t and road_stone_soft(t, "w"):
                seen.add((nf, nr))
                q.append((nf, nr))
    return False


def soft_finish_within(st, depth):
    if has_road_soft(st):
        return True
    if depth <= 0:
        return False
    # Soft placements.
    if st["flats_w"] > 0 or st["caps_w"] > 0:
        for f in range(N):
            for r in range(1, N + 1):
                if st["stacks"][f][r - 1]:
                    continue
                trial = deepcopy(st)
                if st["flats_w"] > 0:
                    trial["stacks"][f][r - 1] = ["w"]
                    trial["flats_w"] = st["flats_w"] - 1
                else:
                    trial["stacks"][f][r - 1] = ["C"]
                    trial["caps_w"] = st["caps_w"] - 1
                if soft_finish_within(trial, depth - 1):
                    return True
    # Soft carry slides (ignores real carry limit).
    for f in range(N):
        for r in range(1, N + 1):
            stack = st["stacks"][f][r - 1]
            if not stack or stack[-1] not in ("w", "W", "C"):
                continue
            for carry in range(1, min(len(stack), SOFT_CARRY) + 1):
                for df, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nf, nr = f + df, r + dr
                    if not (0 <= nf < N and 1 <= nr <= N):
                        continue
                    trial = deepcopy(st)
                    taken = trial["stacks"][f][r - 1][-carry:]
                    del trial["stacks"][f][r - 1][-carry:]
                    # Soft: flatten any standing automatically.
                    dest = trial["stacks"][nf][nr - 1]
                    if dest and dest[-1] in ("W", "B"):
                        dest[-1] = dest[-1].lower()
                    dest.extend(taken)
                    if soft_finish_within(trial, depth - 1):
                        return True
    return False


def ready(st):
    # Depth 2 covers the booklet's cooperative two-gap traps while remaining
    # a surface whisper (standing tops still count; carry soft-limit is 8).
    return soft_finish_within(st, 2)


puzzle_dir = sys.argv[1]
names = sorted(
    n for n in os.listdir(puzzle_dir)
    if n.startswith("board_") and n.endswith(".txt")
)
for name in names:
    st = load(os.path.join(puzzle_dir, name))
    verdict = "ready_lane" if ready(st) else "open_lane"
    print(f"{name[:-4]} {verdict}")
PY
