"""List contest round stems under the puzzle directory."""
from __future__ import annotations

import os


def list_rounds(puzzle_dir: str) -> list[str]:
    names = []
    for name in os.listdir(puzzle_dir):
        if name.startswith("board_") and name.endswith(".txt"):
            names.append(name[:-4])
    return sorted(names)
