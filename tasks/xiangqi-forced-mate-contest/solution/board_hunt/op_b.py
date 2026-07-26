"""Classify one contest sheet into a card row."""
from __future__ import annotations

import sys
from pathlib import Path

# Prefer the oracle-copied engine beside this module.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import xq_engine as xq  # noqa: E402

_apply = xq._apply


def _build_sequence(board):
    budget = xq.FORCE_BUDGET
    seq = []
    b = [row[:] for row in board]
    river = False
    for _ in range(budget):
        best = None
        best_len = 999
        rem = budget - len([s for s in seq if s.startswith("red")])
        for mv in xq.gen_legal(b, "r"):
            nb = _apply(b, mv[1], mv[3], mv[0], mv[2])
            if xq.is_mate(nb, "b"):
                best = mv
                best_len = 1
                break
            replies = xq.gen_legal(nb, "b")
            if not replies or rem <= 1:
                continue
            worst = 0
            ok = True
            for rm in replies:
                nb2 = _apply(nb, rm[1], rm[3], rm[0], rm[2])
                sub = xq.forced_mate_in(nb2, "r", rem - 1)
                if sub is None:
                    ok = False
                    break
                worst = max(worst, 1 + sub)
            if ok and worst < best_len:
                best_len = worst
                best = mv
        if best is None:
            break
        if xq.crosses_river(best):
            river = True
        seq.append(f"red {xq.move_str(best)}")
        b = _apply(b, best[1], best[3], best[0], best[2])
        if xq.is_mate(b, "b"):
            return seq, river
        replies = xq.gen_legal(b, "b")
        worst_rm, worst_v = None, -1
        rem2 = budget - len([s for s in seq if s.startswith("red")])
        for rm in replies:
            nb2 = _apply(b, rm[1], rm[3], rm[0], rm[2])
            sub = xq.forced_mate_in(nb2, "r", rem2)
            v = sub if sub is not None else 99
            if v >= worst_v:
                worst_v, worst_rm = v, rm
        if worst_rm is None:
            break
        if xq.crosses_river(worst_rm):
            river = True
        seq.append(f"black {xq.move_str(worst_rm)}")
        b = _apply(b, worst_rm[1], worst_rm[3], worst_rm[0], worst_rm[2])
    return seq, river


def op_b(sheet_path: str) -> dict:
    board, _ = xq.load_sheet(sheet_path)
    kind, mi, coop = xq.classify(board)
    bid = Path(sheet_path).stem
    row = {
        "board_id": bid,
        "status": kind,
        "mate_in": int(mi or 0),
        "sequence": [],
        "river_cross": False,
        "refutations": [],
        "coop_mate": bool(coop),
    }
    if kind == "win":
        seq, river = _build_sequence(board)
        row["sequence"] = seq
        row["river_cross"] = river
        row["mate_in"] = int(mi)
        row["coop_mate"] = True
    elif kind == "trap":
        refs = []
        for t in xq.threat_moves(board):
            rep = xq.find_refutation(board, t)
            if rep:
                refs.append({"move": t, "reply": rep})
        row["refutations"] = refs
        row["mate_in"] = int(mi or 0)
        row["coop_mate"] = True
    else:
        row["mate_in"] = 0
        row["coop_mate"] = False
        row["river_cross"] = False
    return row
