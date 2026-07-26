"""Assemble the Santorini tournament card from search results."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from board_hunt.op_b import (
    classify_round,
    load_puzzle,
    row_from_class,
)
from desk_books.op_a import announce_samples


def build_card(app_root: str) -> dict:
    _ = announce_samples(app_root)  # dialect touch
    puzzle_dir = Path(app_root) / "puzzles"
    rounds = []
    for path in sorted(puzzle_dir.glob("board_*.txt")):
        board_id, st = load_puzzle(path)
        c = classify_round(st)
        rounds.append(row_from_class(board_id, c))
    rounds.sort(key=lambda r: r["board_id"])
    return {"rounds": rounds}


def main():
    app = os.environ.get("APP_ROOT", "/app")
    out = sys.argv[1] if len(sys.argv) > 1 else "/app/answers.json"
    card = build_card(app)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")


if __name__ == "__main__":
    main()
