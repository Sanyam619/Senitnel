"""Write the canonical tournament card JSON."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from board_hunt.op_b import op_b
from desk_books.op_a import op_a


def op_c(rows: list, dest: str) -> None:
    payload = {"rounds": sorted(rows, key=lambda r: r["board_id"])}
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")


def main(dest: str) -> None:
    app = os.environ.get("APP_ROOT", "/app")
    op_a(str(Path(app) / "history"))
    rows = []
    for sheet in sorted(Path(app).joinpath("puzzles").glob("board_*.txt")):
        rows.append(op_b(sheet))
    op_c(rows, dest)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/app/answers.json")
