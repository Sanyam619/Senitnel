"""List booklet round stems."""
from __future__ import annotations

import glob
import os


def list_rounds(puzzle_dir):
    paths = sorted(glob.glob(os.path.join(puzzle_dir, "board_*.txt")))
    return [os.path.basename(p)[:-4] for p in paths]
