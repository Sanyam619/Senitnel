#!/usr/bin/env python3
"""Assemble the finished contest card from every round file."""
from __future__ import annotations

import glob
import json
import os
import sys

from desk_books.op_a import (
    build_fort_path,
    build_trap_path,
    build_trap_refs,
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
        "key_wall": "",
        "path_len": 0,
        "sequence": [],
        "refutations": [],
        "coop_block": kind != "fort",
    }
    if kind == "win":
        key, seq, plen = build_win_row(state)
        entry["key_wall"] = key
        entry["sequence"] = seq
        entry["path_len"] = plen
        entry["refutations"] = []
    elif kind == "trap":
        entry["key_wall"] = ""
        entry["sequence"] = []
        entry["path_len"] = build_trap_path(state)
        entry["refutations"] = build_trap_refs(state)
    else:
        entry["key_wall"] = ""
        entry["sequence"] = []
        entry["path_len"] = build_fort_path(state)
        entry["refutations"] = []
        if entry["path_len"] is None:
            entry["path_len"] = 0
    return entry


def main(out_path="/output/quoridor-card.json"):
    app = os.environ.get("APP_ROOT", "/app")
    puzzle_dir = os.path.join(app, "puzzles")
    rounds = []
    for path in sorted(glob.glob(os.path.join(puzzle_dir, "board_*.txt"))):
        board_id = os.path.basename(path)[:-4]
        rounds.append(build_round(board_id, path))
    card = {"schema_tag": "quoridor-path-v1", "rounds": rounds}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"filed {out_path} with {len(rounds)} rounds", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/output/quoridor-card.json")
