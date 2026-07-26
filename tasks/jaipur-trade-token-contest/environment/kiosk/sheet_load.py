"""List puzzle sheets for the overnight printer."""
from __future__ import annotations

from pathlib import Path


def list_sheets(root: str | Path | None = None) -> list[Path]:
    base = Path(root or "/app/puzzles")
    return sorted(base.glob("board_*.txt"))
