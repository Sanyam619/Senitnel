"""Classify one Connect Four sheet into a tournament card row."""

from __future__ import annotations

from pathlib import Path

from board_hunt.engine import (
    classify,
    clear_caches,
    parse_grid,
)


def _read_board(sheet: Path):
    rows = []
    board_id = sheet.stem.replace("board_", "")
    inb = False
    for line in sheet.read_text().splitlines():
        t = line.strip()
        if t.startswith("board_id:"):
            board_id = t.split(":", 1)[1].strip()
        elif t == "board:":
            inb = True
        elif inb and t:
            rows.append(t)
            if len(rows) == 6:
                break
    return board_id, parse_grid(rows)


def op_b(sheet: Path, schema_tag: str) -> dict:
    _ = schema_tag
    board_id, board = _read_board(sheet)
    clear_caches()
    info = classify(board)
    return {
        "board_id": board_id,
        "status": info["status"],
        "best_column": info["best_column"],
        "win_in": info["win_in"],
        "sequence": info["sequence"],
        "threats": info["threats"],
        "refutations": info["refutations"],
        "coop_win": info["coop_win"],
    }
