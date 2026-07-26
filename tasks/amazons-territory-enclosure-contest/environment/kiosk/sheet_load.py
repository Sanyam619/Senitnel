"""Thin sheet loader used by the overnight printer."""

from __future__ import annotations

from pathlib import Path


def list_sheets(root: str | Path) -> list[Path]:
    return sorted(Path(root).glob("board_*.txt"))
