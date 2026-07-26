"""List puzzle sheets for the overnight printer."""
from __future__ import annotations

from pathlib import Path


def sheet_paths(root: str | Path) -> list[Path]:
    base = Path(root) / "puzzles"
    return sorted(base.glob("board_*.txt"))
