"""Assemble the finished contest card from every round file."""
from __future__ import annotations

import glob
import json
import os
import sys

from board_hunt.op_b import cell_name, winning_moves
from desk_books.op_a import (
    classify,
    read_board,
    refutation_for,
    threat_cells,
)


def build_round(board_id, path):
    black, white, n = read_board(path)
    kind = classify(black, white, n)
    entry = {
        "board_id": board_id,
        "status": kind,
        "winning_side": "black" if kind == "win" else "white",
        "coop_fillable": kind != "fort",
        "key_cells": [],
        "refutations": [],
    }
    if kind == "win":
        entry["key_cells"] = sorted(
            cell_name(*m) for m in winning_moves(black, white, n)
        )
    elif kind == "trap":
        refs = []
        for c in threat_cells(black, white, n):
            w = refutation_for(black, white, c, n)
            refs.append({"cell": cell_name(*c), "reply": cell_name(*w)})
        entry["refutations"] = sorted(refs, key=lambda x: x["cell"])
    return entry


def main(out_path="/output/hex-card.json"):
    app = os.environ.get("APP_ROOT", "/app")
    puzzle_dir = os.path.join(app, "puzzles")
    rounds = []
    for path in sorted(glob.glob(os.path.join(puzzle_dir, "board_*.txt"))):
        board_id = os.path.basename(path)[:-4]
        rounds.append(build_round(board_id, path))
    card = {"schema_tag": "hex-shore-v1", "rounds": rounds}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"filed {out_path} with {len(rounds)} rounds", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/output/hex-card.json")
