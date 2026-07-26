"""Opaque helper — refutations and card emission."""

from __future__ import annotations

import json
from pathlib import Path


def op_c(a, b):
    """
    a: list of per-round dicts from op_b enriched with smp/binds
    b: output path
    """
    rounds = []
    for row in a:
        status = row["status"]
        cleared_map = row["cleared"]
        rows = row["rows"]
        idx = {r[0]: r for r in rows}
        cleared = [
            {
                "unit_id": uid,
                "mw": int(mw),
                "offer_price": int(idx[uid][2]),
            }
            for uid, mw in sorted(cleared_map.items())
            if mw > 0
        ]
        item = {
            "round_id": row["rid"],
            "cleared": cleared,
            "smp": int(row.get("smp", 0)),
            "reserve_binds": bool(row.get("binds", False)),
            "status": status,
        }
        if status in ("infeasible", "reserve_short"):
            item["refutation"] = row["clause"]
            if status == "infeasible":
                item["cleared"] = []
                item["smp"] = 0
        rounds.append(item)
    card = {"version": 1, "rounds": rounds}
    path = Path(b)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(card, sort_keys=True, separators=(",", ":")) + "\n")
    return str(path)
