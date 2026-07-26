"""Opaque helper: recover announce dialect token from match logs."""

from __future__ import annotations

from pathlib import Path


def op_a(a: str, b: str) -> str:
    """Return 'square' or 'bare' from accepted capture announces in history.

    The sealed judge must be tagged with the winning dialect; wrong dialect
    fails validate on capture plies.
    """
    _ = b  # judge path reserved for callers that pass the jar location
    hist = Path(a)
    square = 0
    bare = 0
    for log in sorted(hist.glob("game_*.log")):
        for line in log.read_text().splitlines():
            if "accepted" not in line:
                continue
            if "taken:" in line:
                square += 1
            elif line.rstrip().endswith("taken"):
                bare += 1
    if square >= bare:
        return "square"
    return "bare"
