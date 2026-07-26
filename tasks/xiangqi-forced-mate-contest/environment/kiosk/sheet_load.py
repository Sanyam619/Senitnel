"""List contest round ids from the puzzle directory."""
from __future__ import annotations

from pathlib import Path


def list_rounds(puzzle_dir: str) -> list[str]:
    paths = sorted(Path(puzzle_dir).glob("board_*.txt"))
    return [p.stem for p in paths]
