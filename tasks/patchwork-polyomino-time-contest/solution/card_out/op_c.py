"""File the finished rows as the tournament card."""

from __future__ import annotations

import json
from pathlib import Path


def op_c(rows: list[dict], schema_tag: str, out_path: str) -> None:
    ordered = sorted(rows, key=lambda r: r["board_id"])
    card = {"schema_tag": schema_tag, "rounds": ordered}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n")
