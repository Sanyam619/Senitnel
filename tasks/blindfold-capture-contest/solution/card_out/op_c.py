"""Opaque helper: attach derived trap refutations and emit the score card."""

from __future__ import annotations

import json
import os
from pathlib import Path

from board_hunt.engine import load_sheet, refute_threat, threat_tries


def op_c(a, b: str) -> None:
    rows = list(a)
    app = Path(os.environ.get("APP_ROOT", "/app"))
    finished = []
    for row in rows:
        row = dict(row)
        threats = row.pop("_threats", None)
        if (
            row.get("status") == "unwinnable"
            and row.get("coop_capturable")
            and row.get("refutations") is None
        ):
            bid = int(row["board_id"])
            sheet = app / "puzzles" / f"board_{bid:02d}.txt"
            sq, _side, mark, _t = load_sheet(sheet)
            if threats is None:
                threats = threat_tries(sq, mark)
            refs = []
            for try_uci in sorted(threats):
                white = refute_threat(sq, mark, try_uci)
                if white is None:
                    raise RuntimeError(f"board {bid}: no refutation for {try_uci}")
                refs.append({"after_black": try_uci, "white": white})
            row["refutations"] = refs
        finished.append(row)
    Path(b).write_text(json.dumps({"boards": finished}, indent=2) + "\n")
