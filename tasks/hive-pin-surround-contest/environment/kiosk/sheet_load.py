"""Round-file reader for the overnight printer."""
from __future__ import annotations

import os


def read_round(path):
    rows = []
    meta = {}
    in_pieces = False
    pieces = []
    with open(path) as fh:
        for line in fh:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if t == "pieces:":
                in_pieces = True
                continue
            if in_pieces:
                pieces.append(t)
                rows.append(t)
                continue
            if ":" in t:
                k, v = t.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, rows


def list_rounds(puzzle_dir):
    names = [
        n for n in os.listdir(puzzle_dir)
        if n.startswith("board_") and n.endswith(".txt")
    ]
    return {n[:-4]: os.path.join(puzzle_dir, n) for n in names}
