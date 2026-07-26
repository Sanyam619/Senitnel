"""Assemble the finished contest card from every round file."""
from __future__ import annotations

import glob
import json
import os
import sys

from board_hunt.op_b import read_board
from desk_books.op_a import (
    build_fort_row,
    build_trap_freedom,
    build_trap_refs,
    build_win_row,
    classify,
)


def build_round(board_id, path):
    state = read_board(path)
    kind = classify(state)
    entry = {
        "board_id": board_id,
        "status": kind,
        "key_bug": "",
        "freedom": 0,
        "sequence": [],
        "refutations": [],
        "coop_pin": kind != "fort",
    }
    if kind == "win":
        key, seq, freedom = build_win_row(state)
        entry["key_bug"] = key
        entry["sequence"] = seq
        entry["freedom"] = freedom
    elif kind == "trap":
        entry["key_bug"] = ""
        entry["sequence"] = []
        entry["freedom"] = build_trap_freedom(state)
        entry["refutations"] = build_trap_refs(state)
    else:
        entry["key_bug"] = ""
        entry["sequence"] = []
        entry["freedom"] = build_fort_row(state)
        entry["refutations"] = []
    return entry


def main(out_path="/output/hive-card.json"):
    app = os.environ.get("APP_ROOT", "/app")
    puzzle_dir = os.path.join(app, "puzzles")
    rounds = []
    for path in sorted(glob.glob(os.path.join(puzzle_dir, "board_*.txt"))):
        board_id = os.path.basename(path)[:-4]
        rounds.append(build_round(board_id, path))
    card = {"schema_tag": "hive-pin-v1", "rounds": rounds}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"filed {out_path} with {len(rounds)} rounds", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/output/hive-card.json")
