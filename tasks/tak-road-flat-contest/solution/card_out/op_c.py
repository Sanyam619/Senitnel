"""Assemble the tournament card from sealed puzzle sheets."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from desk_books.op_a import (
    apply_token,
    build_trap_refs,
    classify,
    coop_road_len,
    find_forcing_sequence,
    key_square_of,
    read_board,
    white_road_len,
    winning_first_moves,
)

SCHEMA_TAG = "tak-road-v1"
APP_ROOT = Path(os.environ.get("APP_ROOT", "/app"))


def build_round(board_id: str, path: Path) -> dict:
    state = read_board(str(path))
    status = classify(state)
    if status == "win":
        seq = find_forcing_sequence(state)
        assert seq, f"no forcing sequence for {board_id}"
        # Prefer a winning first move that matches seq[0].
        first = seq[0]
        wins = winning_first_moves(state)
        assert first in wins, f"{board_id}: {first} not forcing"
        cur = state
        for tok in seq:
            nxt = apply_token(cur, tok)
            assert nxt is not None, f"{board_id}: illegal {tok}"
            cur = nxt
        road = white_road_len(cur)
        assert road is not None and road >= 5
        return {
            "board_id": board_id,
            "status": "win",
            "coop_road": True,
            "key_square": key_square_of(first),
            "road_len": road,
            "sequence": seq,
            "refutations": [],
        }
    if status == "trap":
        return {
            "board_id": board_id,
            "status": "trap",
            "coop_road": True,
            "key_square": "",
            "road_len": coop_road_len(state),
            "sequence": [],
            "refutations": build_trap_refs(state),
        }
    return {
        "board_id": board_id,
        "status": "fort",
        "coop_road": False,
        "key_square": "",
        "road_len": 0,
        "sequence": [],
        "refutations": [],
    }


def main(out_path: str) -> None:
    puzzles = sorted((APP_ROOT / "puzzles").glob("board_*.txt"))
    assert len(puzzles) == 11
    rounds = [build_round(p.name[:-4], p) for p in puzzles]
    card = {"schema_tag": SCHEMA_TAG, "rounds": rounds}
    Path(out_path).write_text(json.dumps(card, separators=(",", ":"), sort_keys=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/app/answers.json")
