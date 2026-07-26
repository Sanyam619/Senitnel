"""Overnight printer draft logic.

Quick in-house reading: ask the sensei whisper whether each round still
looks blocked along White's corridor, and stamp a verdict from that. This
is a draft only; the sealed table judge and the scoring rules decide the
real card.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from sheet_load import list_rounds


def sensei_reading(tool, puzzle_dir):
    out = subprocess.run(
        [tool, puzzle_dir], capture_output=True, text=True, check=True
    ).stdout
    reading = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2:
            reading[parts[0]] = parts[1]
    return reading


def draft_row(board_id, look):
    # Naive stamp straight from the corridor whisper.
    if look == "looks_blocked":
        return {
            "board_id": board_id,
            "status": "win",
            "coop_block": True,
            "key_wall": "",
            "path_len": 7,
            "sequence": [],
            "refutations": [],
        }
    return {
        "board_id": board_id,
        "status": "fort",
        "coop_block": False,
        "key_wall": "",
        "path_len": 4,
        "sequence": [],
        "refutations": [],
    }


def _complete_card(card):
    if not isinstance(card, dict):
        return False
    if card.get("schema_tag") != "quoridor-path-v1":
        return False
    rounds = card.get("rounds")
    return isinstance(rounds, list) and len(rounds) == 11


def file_existing(path):
    with open(path) as fh:
        card = json.load(fh)
    if not _complete_card(card):
        return False
    card["rounds"] = sorted(card["rounds"], key=lambda row: row["board_id"])
    staged = f"{path}.staged"
    with open(staged, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(staged, path)
    return True


def main():
    app = os.environ.get("APP_ROOT", "/app")
    puzzle_dir = os.path.join(app, "puzzles")
    tool = os.path.join(app, "tools", "sensei_hint.sh")
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/output/quoridor-card.json"

    if os.path.exists(out_path) and file_existing(out_path):
        print(f"filed existing card to {out_path}", file=sys.stderr)
        return

    rounds = list_rounds(puzzle_dir)
    look = sensei_reading(tool, puzzle_dir)
    card = {"schema_tag": "quoridor-path-v1", "rounds": []}
    for board_id in sorted(rounds):
        card["rounds"].append(draft_row(board_id, look.get(board_id, "open_lane")))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(
        f"printed draft to {out_path} ({len(card['rounds'])} rounds)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
