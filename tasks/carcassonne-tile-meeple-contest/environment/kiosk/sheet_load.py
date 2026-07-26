"""List puzzle sheets for the overnight printer."""

from __future__ import annotations

from pathlib import Path


def list_sheets(root: str = "/app") -> list[Path]:
    return sorted(Path(root).joinpath("puzzles").glob("board_*.txt"))
