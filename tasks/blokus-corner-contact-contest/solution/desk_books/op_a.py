"""Desk helper: load booklet sheets in id order."""

from __future__ import annotations

from pathlib import Path


def sheets(puzzle_dir: str) -> list[Path]:
    return sorted(Path(puzzle_dir).glob("board_*.txt"))


def op_a(history_dir: str) -> str:
    """Confirm match-log dialect folder is present; return a desk token."""
    root = Path(history_dir)
    logs = sorted(root.glob("game_*.log"))
    if not logs:
        raise FileNotFoundError("no match logs on the desk")
    return "blokus-corner-v1"
