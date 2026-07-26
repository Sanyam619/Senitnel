"""Desk books: confirm match-log dialect samples; return schema token."""

from __future__ import annotations

from pathlib import Path


def op_a(history_dir: str) -> str:
    root = Path(history_dir)
    logs = sorted(root.glob("game_*.log"))
    if len(logs) < 2:
        raise RuntimeError("match logs missing")
    for path in logs:
        text = path.read_text().strip()
        if "red " not in text and "blue " not in text:
            raise RuntimeError(f"empty dialect sample {path.name}")
    return "carcassonne-meeple-v1"
