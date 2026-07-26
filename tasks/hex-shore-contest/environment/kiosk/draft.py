"""Overnight printer draft logic.

Quick in-house reading: ask the sensei whisper whether each round still
looks fillable, and stamp a verdict from that. This is a draft only; the
sealed table judge and the scoring rules decide the real card.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from sheet_load import list_rounds


def sensei_reading(tool, puzzle_dir):
    out = subprocess.run([tool, puzzle_dir], capture_output=True,
                         text=True, check=True).stdout
    reading = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2:
            reading[parts[0]] = parts[1]
    return reading


def draft_row(board_id, look):
    # Naive stamp straight from the fillability whisper.
    if look == "looks_fillable_if_uncontested":
        return {
            "board_id": board_id,
            "status": "win",
            "winning_side": "black",
            "coop_fillable": True,
            "key_cells": [],
            "refutations": [],
        }
    return {
        "board_id": board_id,
        "status": "fort",
        "winning_side": "black",
        "coop_fillable": False,
        "key_cells": [],
        "refutations": [],
    }


def file_existing(path):
    with open(path) as fh:
        card = json.load(fh)
    card["rounds"] = sorted(card["rounds"], key=lambda row: row["board_id"])
    staged = f"{path}.staged"
    with open(staged, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(staged, path)


def main():
    app = os.environ.get("APP_ROOT", "/app")
    puzzle_dir = os.path.join(app, "puzzles")
    tool = os.path.join(app, "tools", "sensei_hint.sh")
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/output/hex-card.json"

    if os.path.exists(out_path):
        file_existing(out_path)
        print(f"filed existing card to {out_path}", file=sys.stderr)
        return

    rounds = list_rounds(puzzle_dir)
    look = sensei_reading(tool, puzzle_dir)
    # Draft walks the rounds as they come back from the directory listing.
    card = {"schema_tag": "hex-shore-v1", "rounds": []}
    for board_id in set(rounds):
        card["rounds"].append(draft_row(board_id, look.get(board_id, "walled_off")))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(card, fh, indent=2)
    print(f"printed draft to {out_path} ({len(card['rounds'])} rounds)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
