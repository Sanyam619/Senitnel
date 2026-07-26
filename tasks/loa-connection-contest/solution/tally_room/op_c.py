"""Assemble the finished contest card from every round sheet."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from desk_books.op_a import (
    build_trap_refs,
    classify,
    forcing_line,
    read_board,
    scored_components,
)

SCHEMA_TAG = "loa-connection-v1"
APP_ROOT = Path(os.environ.get("APP_ROOT", "/app"))


def build_round(board_id, path):
    mine, theirs, size = read_board(str(path))
    verdict = classify(mine, theirs, size)
    entry = {
        "board_id": board_id,
        "status": verdict,
        "key_move": "",
        "components": scored_components(mine, theirs, size, verdict),
        "sequence": [],
        "refutations": [],
        "coop_connect": verdict != "fort",
    }
    if verdict == "win":
        line = forcing_line(mine, theirs, size)
        assert line, f"no forcing line for {board_id}"
        entry["key_move"] = line[0]
        entry["sequence"] = line
        assert entry["components"] == 1, board_id
    elif verdict == "trap":
        entry["refutations"] = build_trap_refs(mine, theirs, size)
    return entry


def main(out_path):
    sheets = sorted((APP_ROOT / "puzzles").glob("board_*.txt"))
    assert len(sheets) == 12, f"expected twelve rounds, saw {len(sheets)}"
    rounds = [build_round(p.name[:-4], p) for p in sheets]
    card = {"schema_tag": SCHEMA_TAG, "rounds": rounds}
    target = Path(out_path)
    if target.parent and str(target.parent) not in ("", "."):
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n")
    print(f"filed {out_path} with {len(rounds)} rounds", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/output/loa-card.json")
