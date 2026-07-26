"""List puzzle sheets for the overnight printer."""

from __future__ import annotations

from pathlib import Path


def list_sheets(root: Path) -> list[Path]:
    return sorted((root / "puzzles").glob("board_*.txt"))
