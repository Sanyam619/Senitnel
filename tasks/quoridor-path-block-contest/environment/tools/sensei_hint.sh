#!/bin/bash
# Sensei whisper - greedy corridor guess only.
#
# For each round it finds one shortest White path to the south edge, then
# checks whether a wall can cover the first step of that corridor. If the
# first step can be fenced, it prints looks_blocked; otherwise open_lane.
# That is a local corridor guess, NOT a full detour search and NOT the
# contest verdict: a round can look blocked here and still be a fighting
# trap once White answers.
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
from collections import deque

N = 5
FILES = "abcde"


def parse_cell(name):
    return FILES.index(name[0]), int(name[1:])


def parse_wall(wid):
    return wid[0], *parse_cell(wid[2:])


def wall_ok(orient, f, r):
    return orient in ("h", "v") and 0 <= f <= 3 and 1 <= r <= 4


def segments(orient, f, r):
    out = []
    if orient == "h":
        for df in (0, 1):
            out.append(frozenset(((f + df, r), (f + df, r + 1))))
    else:
        for dr in (0, 1):
            out.append(frozenset(((f, r + dr), (f + 1, r + dr))))
    return out


def center(orient, f, r):
    return (f + 1, r + 1)


def conflict(walls, wid):
    o, f, r = parse_wall(wid)
    if not wall_ok(o, f, r) or wid in walls:
        return True
    existing = set()
    cents = {}
    for w in walls:
        wo, wf, wr = parse_wall(w)
        for s in segments(wo, wf, wr):
            existing.add(s)
        cents.setdefault(center(wo, wf, wr), set()).add(wo)
    for s in segments(o, f, r):
        if s in existing:
            return True
    c = center(o, f, r)
    if c in cents and (cents[c] - {o}):
        return True
    return False


def all_walls():
    for orient in ("h", "v"):
        for f in range(4):
            for r in range(1, 5):
                yield f"{orient}-{FILES[f]}{r}"


def load(path):
    walls, rows, inb = [], [], False
    black = white = None
    with open(path) as fh:
        for line in fh:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if t == "board:":
                inb = True
                continue
            if inb:
                rows.append(t)
                continue
            if t.startswith("walls:"):
                walls = t.split(":", 1)[1].split()
    for i, row in enumerate(rows):
        rank = 5 - i
        for f, ch in enumerate(row):
            if ch == "B":
                black = (f, rank)
            elif ch == "W":
                white = (f, rank)
    return black, white, set(walls)


def neighbors(pos, other, segs):
    f, r = pos
    for df, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nf, nr = f + df, r + dr
        if not (0 <= nf < N and 1 <= nr <= N):
            continue
        nxt = (nf, nr)
        if nxt == other:
            continue
        if frozenset((pos, nxt)) in segs:
            continue
        yield nxt


def one_path(white, black, walls):
    segs = set()
    for w in walls:
        o, f, r = parse_wall(w)
        segs.update(segments(o, f, r))
    if white[1] == 1:
        return [white]
    q = deque([(white, [white])])
    seen = {white}
    while q:
        pos, path = q.popleft()
        for nxt in neighbors(pos, black, segs):
            if nxt in seen:
                continue
            np = path + [nxt]
            if nxt[1] == 1:
                return np
            seen.add(nxt)
            q.append((nxt, np))
    return None


def looks_blocked(path, walls):
    if path is None or len(path) < 2:
        return False
    edge = frozenset((path[0], path[1]))
    for wid in all_walls():
        o, f, r = parse_wall(wid)
        if edge not in segments(o, f, r):
            continue
        if conflict(walls, wid):
            continue
        return True
    return False


puzzle_dir = sys.argv[1]
names = sorted(
    n for n in os.listdir(puzzle_dir)
    if n.startswith("board_") and n.endswith(".txt")
)
for name in names:
    black, white, walls = load(os.path.join(puzzle_dir, name))
    path = one_path(white, black, walls)
    verdict = "looks_blocked" if looks_blocked(path, walls) else "open_lane"
    print(f"{name[:-4]} {verdict}")
PY
