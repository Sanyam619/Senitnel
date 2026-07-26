"""Solve one round sheet into a filed card row."""

from __future__ import annotations

from pathlib import Path

from board_hunt import engine as E


def op_b(sheet_path: str, _dialect: str) -> dict:
    E._fit_cache.clear()
    board = E.parse_board(Path(sheet_path).read_text())
    return E.build_round(board)
