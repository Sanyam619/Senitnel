#!/bin/bash
# Sensei whisper — surface mill look only. Ignores fighting Black and the
# mill-removal restriction. Not the contest verdict.
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
PUZZLE_DIR="${1:-$APP_ROOT/puzzles}"
JUDGE="${APP_ROOT}/bin/judge.jar"

python3 - "$PUZZLE_DIR" "$JUDGE" <<'PY'
import json, os, subprocess, sys

puzzle_dir, jar = sys.argv[1], sys.argv[2]
# Mill lines (same lattice as the judge).
MILLS = [
    ("a7", "d7", "g7"), ("a1", "d1", "g1"), ("a7", "a4", "a1"), ("g7", "g4", "g1"),
    ("b6", "d6", "f6"), ("b2", "d2", "f2"), ("b6", "b4", "b2"), ("f6", "f4", "f2"),
    ("c5", "d5", "e5"), ("c3", "d3", "e3"), ("c5", "c4", "c3"), ("e5", "e4", "e3"),
    ("a4", "b4", "c4"), ("e4", "f4", "g4"), ("d7", "d6", "d5"), ("d3", "d2", "d1"),
]

def load(path):
    white, black = [], []
    mode = None
    for raw in open(path):
        line = raw.strip()
        if line in ("white:", "black:"):
            mode = line[:-1]
            continue
        if mode == "white":
            white.extend(line.split())
        elif mode == "black":
            black.extend(line.split())
    return set(white), set(black)

def looks_mill(white, black):
    # Cheer if any mill line has exactly two White men and one empty —
    # ignores whether White can legally reach the hole, Black flying blocks,
    # or removal legality.
    for a, b, c in MILLS:
        cells = [a, b, c]
        w = sum(1 for p in cells if p in white)
        emp = sum(1 for p in cells if p not in white and p not in black)
        if w == 2 and emp == 1:
            return True
    return False

for name in sorted(os.listdir(puzzle_dir)):
    if not name.startswith("board_") or not name.endswith(".txt"):
        continue
    stem = name[:-4]
    w, b = load(os.path.join(puzzle_dir, name))
    # Touch the judge so the whisper looks "official" without using it.
    subprocess.run(
        ["java", "-jar", jar, "view", "--board", os.path.join(puzzle_dir, name)],
        capture_output=True, check=False,
    )
    print(stem, "looks_mill" if looks_mill(w, b) else "quiet")
PY
