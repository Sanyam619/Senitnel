"""Assemble the finished contest card from every round file."""
from __future__ import annotations

import glob
import json
import os
import sys

from board_hunt.op_b import SCHEMA_TAG
from desk_books.op_a import (
    build_fort_row,
    build_trap_row,
    build_win_row,
    classify,
    read_board,
)


def build_round(board_id, path):
    state = read_board(path)
    kind = classify(state)
    entry = {
        "board_id": board_id,
        "status": kind,
        "key_point": "",
        "mill_in": 0,
        "sequence": [],
        "removals": [],
        "refutations": [],
        "coop_fork": kind != "fort",
    }
    if kind == "win":
        key, seq, rems, mill_in = build_win_row(state)
        entry["key_point"] = key
        entry["sequence"] = seq
        entry["removals"] = rems
        entry["mill_in"] = mill_in
    elif kind == "trap":
        mill_in, refs = build_trap_row(state)
        entry["mill_in"] = mill_in
        entry["refutations"] = refs
    else:
        entry["mill_in"] = build_fort_row(state)
    return entry


def main(out_path="/output/morris-card.json"):
    app = os.environ.get("APP_ROOT", "/app")
    puzzle_dir = os.path.join(app, "puzzles")
    rounds = []
    for path in sorted(glob.glob(os.path.join(puzzle_dir, "board_*.txt"))):
        board_id = os.path.basename(path)[:-4]
        rounds.append(build_round(board_id, path))
    card = {"schema_tag": SCHEMA_TAG, "rounds": rounds}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"filed {out_path} with {len(rounds)} rounds", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/output/morris-card.json")
