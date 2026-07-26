"""Write the ordered tournament card."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def op_c(rows: list, out_path: str) -> None:
    app = os.environ.get("APP_ROOT", "/app")
    sys.path.insert(0, app)
    from board_hunt.op_b import op_b
    from desk_books.op_a import op_a

    if rows is None:
        puzzles = sorted(Path(app).joinpath("puzzles").glob("board_*.txt"))
        rows = [op_b(str(p)) for p in puzzles]
    tag = op_a(os.path.join(app, "docs"))
    card = {
        "schema_tag": tag,
        "rounds": sorted(rows, key=lambda r: r["board_id"]),
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(card, fh, indent=2, sort_keys=True)
        fh.write("\n")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/output/xiangqi-card.json"
    op_c(None, out)
