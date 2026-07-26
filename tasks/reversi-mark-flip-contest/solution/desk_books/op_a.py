"""Desk books: read the round sheets and pick up the table's announce dialect."""

from __future__ import annotations

import re
from pathlib import Path

STEP = re.compile(r"\b(black|white) ([a-h][1-8])\|(flips:\d+[^ ]*)")


def op_a(history_dir: str) -> str:
    """The suffix earlier tables added when a call landed on a corner."""
    corners = {"a1", "h1", "a8", "h8"}
    for log in sorted(Path(history_dir).glob("game_*.log")):
        for line in log.read_text().splitlines():
            for _, square, tag in STEP.findall(line):
                if square in corners and "+" in tag:
                    return "+" + tag.split("+", 1)[1]
    return "+corner"


def load_sheet(path: str | Path):
    """Return (board_id, black_mask, white_mask, mark_index) for one sheet."""
    board_id = ""
    mark = -1
    rows: list[str] = []
    reading = False
    for raw in Path(path).read_text().splitlines():
        text = raw.strip()
        if not text:
            continue
        if reading and len(text) == 8 and len(rows) < 8:
            rows.append(text)
            continue
        if text.startswith("board_id:"):
            board_id = text.split(":", 1)[1].strip()
        elif text.startswith("mark:"):
            name = text.split(":", 1)[1].strip()
            mark = (ord(name[1]) - ord("1")) * 8 + (ord(name[0]) - ord("a"))
        elif text.startswith("board:"):
            reading = True
    if len(rows) != 8 or mark < 0:
        raise ValueError(f"unreadable sheet {path}")
    black = white = 0
    for offset, row in enumerate(reversed(rows)):
        for file_index, disc in enumerate(row):
            spot = 1 << (offset * 8 + file_index)
            if disc == "B":
                black |= spot
            elif disc == "W":
                white |= spot
    return board_id, black, white, mark


def sheets(puzzle_dir: str):
    return [load_sheet(p) for p in sorted(Path(puzzle_dir).glob("board_*.txt"))]
