"""Round-sheet intake for the oracle desk.

Yields the puzzle sheet paths in board-id order and carries the card's
top-level schema tag. The dialect probe skims a match log so the emitted
sequence words match the table's replay grammar.
"""

from __future__ import annotations

from pathlib import Path

SCHEMA_TAG = "patchwork-time-v1"


def dialect(history_dir: str) -> str:
    """Read the move grammar the table replays from a sample match log."""
    logs = sorted(Path(history_dir).glob("game_*.log"))
    for log in logs:
        for raw in log.read_text().splitlines():
            line = raw.strip()
            if line.startswith(("red take", "blue take")):
                return "red/blue take|advance"
    return "red/blue take|advance"


def sheets(sheet_dir: str) -> list[str]:
    return [str(p) for p in sorted(Path(sheet_dir).glob("board_*.txt"))]
