"""Write the canonical tournament card JSON."""

from __future__ import annotations

import json
import os
from pathlib import Path


def op_c(rows: list, dest: str) -> None:
    card = {
        "schema_tag": "onitama-temple-v1",
        "rounds": sorted(rows, key=lambda r: r["board_id"]),
    }
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_suffix(path.suffix + ".staged")
    staged.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n")
    os.replace(staged, path)


if __name__ == "__main__":
    import sys

    app = Path(os.environ.get("APP_ROOT", "/app"))
    sys.path.insert(0, str(app))
    from board_hunt.op_b import op_b
    from desk_books.op_a import op_a

    schema = op_a(str(app / "history"))
    sheets = sorted((app / "puzzles").glob("board_*.txt"))
    rows = [op_b(p, schema) for p in sheets]
    out = sys.argv[1] if len(sys.argv) > 1 else "/app/answers.json"
    op_c(rows, out)
