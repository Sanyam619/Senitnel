#!/bin/bash
# Sensei whisper — surface summit look only. Ignores dome blocks and fighting
# Second. Not the contest verdict.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
PUZZLE_DIR="${1:-$APP_ROOT/puzzles}"
JUDGE="${APP_ROOT}/bin/judge.jar"

python3 - "$PUZZLE_DIR" "$JUDGE" <<'PY'
import json, os, subprocess, sys

puzzle_dir, jar = sys.argv[1], sys.argv[2]
FILES = "abcde"
DIRS = [(df, dr) for df in (-1, 0, 1) for dr in (-1, 0, 1) if not (df == 0 and dr == 0)]

def nbrs(sq):
    f, r = FILES.index(sq[0]), int(sq[1]) - 1
    out = []
    for df, dr in DIRS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 5 and 0 <= nr < 5:
            out.append(FILES[nf] + str(nr + 1))
    return out

def load(path):
    heights = {}
    first, second = [], []
    rows = []
    in_h = False
    for raw in open(path):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "heights:":
            in_h = True
            continue
        if line.startswith("first:"):
            in_h = False
            first = line.split(":", 1)[1].split()
            continue
        if line.startswith("second:"):
            in_h = False
            second = line.split(":", 1)[1].split()
            continue
        if in_h:
            rows.append(line.split())
    for ri, row in enumerate(rows):
        rank = 5 - ri
        for ci, cell in enumerate(row):
            sq = FILES[ci] + str(rank)
            # Sensei treats domes as climbable level-3 peaks.
            if cell in ("D", "d"):
                heights[sq] = 3
            else:
                heights[sq] = int(cell)
    return heights, first, second

def looks_ready(heights, first, second):
    occ = set(first) | set(second)
    # Cheer if any First worker sits on height >=1 next to a peak (h>=3),
    # ignoring whether the peak is truly domed or occupied.
    for fr in first:
        hf = heights.get(fr, 0)
        for to in nbrs(fr):
            ht = heights.get(to, 0)
            if ht >= 3 and (ht - hf) <= 2:  # soft climb; ignores dome/occ
                if to not in occ or to in first:
                    return True
            # also cheer a two-step "build then climb" silhouette
            if hf >= 1 and ht >= 2 and to not in occ:
                for peak in nbrs(to):
                    if heights.get(peak, 0) >= 3:
                        return True
    return False

for name in sorted(os.listdir(puzzle_dir)):
    if not name.startswith("board_") or not name.endswith(".txt"):
        continue
    stem = name[:-4]
    path = os.path.join(puzzle_dir, name)
    h, f, s = load(path)
    subprocess.run(
        ["java", "-jar", jar, "view", "--board", path],
        capture_output=True, check=False,
    )
    print(stem, "looks_ready" if looks_ready(h, f, s) else "quiet")
PY
