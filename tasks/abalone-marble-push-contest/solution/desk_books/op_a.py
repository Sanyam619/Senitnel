"""Desk books: confirm the match-log dialect samples read cleanly."""

from __future__ import annotations

from pathlib import Path


def op_a(history_dir: str) -> None:
    root = Path(history_dir)
    logs = sorted(root.glob("game_*.log"))
    if len(logs) < 2:
        raise RuntimeError("match logs missing")
    for path in logs:
        text = path.read_text().strip()
        if "black " not in text and "white " not in text:
            raise RuntimeError(f"empty dialect sample {path.name}")
