"""Card out: file the finished tournament card."""

from __future__ import annotations

import json
from pathlib import Path


def op_c(rows: list[dict], card_path: str) -> None:
    card = {"rounds": sorted(rows, key=lambda row: row["board_id"])}
    target = Path(card_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(card, indent=2, sort_keys=False) + "\n")
