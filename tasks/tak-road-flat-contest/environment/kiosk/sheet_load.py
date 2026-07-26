"""Load puzzle sheets for the overnight printer."""
from __future__ import annotations

from pathlib import Path


def list_boards(root: Path) -> list[Path]:
    return sorted(root.glob("board_*.txt"))


def board_id(path: Path) -> str:
    return path.name[:-4]
