"""Round-sheet reader for the overnight printer."""
from __future__ import annotations

import os


def read_round(path):
    rows = []
    in_board = False
    meta = {}
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
            elif ":" in t:
                k, v = t.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta, rows


def list_rounds(puzzle_dir):
    names = [
        n for n in os.listdir(puzzle_dir)
        if n.startswith("board_") and n.endswith(".txt")
    ]
    return {n[:-4]: os.path.join(puzzle_dir, n) for n in names}


def piece_squares(rows, glyph):
    return [
        (r, c)
        for r, row in enumerate(rows)
        for c, ch in enumerate(row)
        if ch == glyph
    ]
