"""List puzzle sheets for the overnight printer."""

from __future__ import annotations

from pathlib import Path


def list_sheets(puzzle_dir: Path) -> list[Path]:
    return sorted(puzzle_dir.glob("board_*.txt"))
