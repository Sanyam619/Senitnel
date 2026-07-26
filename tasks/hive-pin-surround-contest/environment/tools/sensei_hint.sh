#!/bin/bash
# Sensei whisper - quick reach guess only.
#
# For each round it looks at the black queen's current empty neighbors and
# asks whether some distinct White piece could land on each one using that
# piece's basic step/jump/slide shape. It does NOT check the one-hive
# continuity rule and does NOT check the sliding gate rule (the two
# hexes shared with the origin), so a shape that looks reachable here can
# still be illegal at the table. That is a quick reach guess, NOT a full
# search and NOT the contest verdict: a round can look pinned here and
# still be a fighting trap once Black answers, or even a fort once the
# dropped checks are restored.
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

DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def neighbors(cell):
    return [add(cell, d) for d in DIRS]


def load(path):
    pieces = {}
    in_pieces = False
    with open(path) as fh:
        for line in fh:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if t == "pieces:":
                in_pieces = True
                continue
            if in_pieces:
                parts = t.split()
                pid, qs, rs, hs = parts[0], parts[1], parts[2], parts[3]
                color = "white" if pid.startswith("W") else "black"
                kind = pid.split("-")[1][0]
                pieces[pid] = (color, kind, int(qs), int(rs), int(hs))
    return pieces


def occupied(pieces, skip=None):
    return {(q, r) for pid, (_c, _k, q, r, _h) in pieces.items() if pid != skip}


def touches(cell, occ):
    return any(n in occ for n in neighbors(cell))


def loose_dests(pieces, pid):
    color, kind, q, r, _h = pieces[pid]
    start = (q, r)
    occ = occupied(pieces, skip=pid)
    if kind == "Q":
        return [n for n in neighbors(start) if n not in occ]
    if kind == "B":
        return list(neighbors(start))
    if kind == "G":
        out = []
        for d in DIRS:
            cur = add(start, d)
            if cur not in occ:
                continue
            while cur in occ:
                cur = add(cur, d)
            out.append(cur)
        return out
    # Spider / Ant: perimeter walk with no gate check.
    limit = 3 if kind == "S" else 20
    seen = {start: 0}
    found = {}
    q_bfs = deque([(start, 0)])
    while q_bfs:
        cur, dist = q_bfs.popleft()
        if kind == "S":
            if dist == limit and cur != start and cur not in occ and touches(cur, occ):
                found[cur] = dist
            if dist >= limit:
                continue
        else:
            if dist > 0 and cur != start and cur not in occ and touches(cur, occ):
                found[cur] = dist
            if dist >= limit:
                continue
        for nxt in neighbors(cur):
            if nxt in occ:
                continue
            if nxt != start and not touches(nxt, occ):
                continue
            if nxt in seen and seen[nxt] <= dist + 1:
                continue
            seen[nxt] = dist + 1
            q_bfs.append((nxt, dist + 1))
    return list(found)


def matches(holes, cover):
    def rec(i, used):
        if i == len(holes):
            return True
        for pid in cover.get(holes[i], []):
            if pid in used:
                continue
            used.add(pid)
            if rec(i + 1, used):
                return True
            used.discard(pid)
        return False

    return rec(0, set())


def looks_pinned(pieces):
    qcell = None
    for pid, (color, kind, q, r, _h) in pieces.items():
        if color == "black" and kind == "Q":
            qcell = (q, r)
    if qcell is None:
        return False
    occ = occupied(pieces)
    holes = [n for n in neighbors(qcell) if n not in occ]
    if not holes:
        return True
    white = [pid for pid, (c, _k, _q, _r, _h) in pieces.items() if c == "white"]
    cover = {h: [] for h in holes}
    for pid in white:
        for d in loose_dests(pieces, pid):
            if d in cover:
                cover[d].append(pid)
    return matches(holes, cover)


puzzle_dir = sys.argv[1]
names = sorted(
    n for n in os.listdir(puzzle_dir)
    if n.startswith("board_") and n.endswith(".txt")
)
for name in names:
    pieces = load(os.path.join(puzzle_dir, name))
    verdict = "looks_pinned" if looks_pinned(pieces) else "open_lane"
    print(f"{name[:-4]} {verdict}")
PY
