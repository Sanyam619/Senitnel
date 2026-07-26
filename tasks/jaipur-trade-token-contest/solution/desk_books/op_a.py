"""Confirm match logs present; return schema token."""
from __future__ import annotations

from pathlib import Path


def op_a(history_dir: str) -> str:
    root = Path(history_dir)
    logs = sorted(root.glob("game_*.log"))
    if len(logs) < 2:
        raise FileNotFoundError("match logs missing")
    for path in logs:
        if path.stat().st_size <= 0:
            raise ValueError(f"empty log {path.name}")
    return "jaipur-trade-v1"
