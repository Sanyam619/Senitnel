"""Emit the tournament card as canonical JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def op_c(rows: list[dict], dest: str) -> None:
    ordered = sorted(rows, key=lambda r: r["board_id"])
    card = {"schema_tag": "amazons-territory-v1", "rounds": ordered}
    Path(dest).write_text(json.dumps(card, indent=2, sort_keys=False) + "\n")


if __name__ == "__main__":
    # Standalone path used by derive.sh double-emit check.
    import os

    app = os.environ.get("APP_ROOT", "/app")
    sys.path.insert(0, app)
    from board_hunt.op_b import op_b
    from desk_books.op_a import op_a, sheets

    dialect = op_a(app + "/history")
    rows = [op_b(sheet, dialect) for sheet in sheets(app + "/puzzles")]
    dest = sys.argv[1] if len(sys.argv) > 1 else "/output/amazons-card.json"
    op_c(rows, dest)
