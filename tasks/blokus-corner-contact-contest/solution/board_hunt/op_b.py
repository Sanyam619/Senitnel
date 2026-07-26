"""Classify one sheet into a card row."""
from __future__ import annotations

from pathlib import Path

from board_hunt.engine import (
    BLUE,
    BUDGET,
    YELLOW,
    all_placements,
    apply,
    can_coop,
    can_force,
    filled,
    fmt_placement,
    parse_board_text,
    spot,
    sq_left,
    threats,
    verdict,
)


def _coop_line(cells, binv, yinv, stones=BUDGET):
    if filled(binv):
        return []
    if stones <= 0:
        return None
    for pid, place in all_placements(cells, BLUE, binv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        step = f"blue {fmt_placement(pid, place)}"
        if filled(nb):
            return [step]
        rest = _coop_line(after, nb, yinv, stones - 1)
        if rest is not None:
            return [step] + rest
    return None


def _force_line(cells, binv, yinv, stones=BUDGET):
    if filled(binv):
        return []
    if stones <= 0:
        return None
    for pid, place in all_placements(cells, BLUE, binv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        step = f"blue {fmt_placement(pid, place)}"
        if filled(nb):
            return [step]
        if stones == 1:
            continue
        ymoves = all_placements(after, YELLOW, yinv)
        if not ymoves:
            rest = _force_line(after, nb, yinv, stones - 1)
            if rest is not None:
                return [step] + rest
            continue
        if all(
            can_force(
                apply(after, YELLOW, yp, ypl, yinv)[0],
                nb,
                apply(after, YELLOW, yp, ypl, yinv)[1],
                stones - 1,
            )
            for yp, ypl in ymoves
        ):
            yp, ypl = ymoves[0]
            ya, ny = apply(after, YELLOW, yp, ypl, yinv)
            rest = _force_line(ya, nb, ny, stones - 1)
            if rest is not None:
                return [step, f"yellow {fmt_placement(yp, ypl)}"] + rest
    return None


def _refutations(cells, binv, yinv):
    rows = []
    for pid, place in threats(cells, binv, yinv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        for yp, ypl in all_placements(after, YELLOW, yinv):
            ya, _ny = apply(after, YELLOW, yp, ypl, yinv)
            still = any(
                filled(apply(ya, BLUE, p2, pl2, nb)[1])
                for p2, pl2 in all_placements(ya, BLUE, nb)
            )
            if not still:
                rows.append({"piece_id": pid, "reply": fmt_placement(yp, ypl)})
                break
    return rows


def _replay_squares(cells, binv, yinv, sequence):
    board, bi, yi = cells, binv, yinv
    for step in sequence:
        colour, mv = step.split(" ", 1)
        pid, rest = mv.split("@", 1)
        place = tuple(sorted(spot(x) for x in rest.split(",")))
        who = BLUE if colour == "blue" else YELLOW
        inv = bi if who == BLUE else yi
        board, ninv = apply(board, who, pid, place, inv)
        if who == BLUE:
            bi = ninv
        else:
            yi = ninv
    return sq_left(bi)


def op_b(sheet: Path, schema_tag: str) -> dict:
    _ = schema_tag
    bid, cells, binv, yinv = parse_board_text(sheet.read_text())
    can_force.cache_clear()
    can_coop.cache_clear()
    v = verdict(cells, binv, yinv)
    coop = v in ("win", "trap")
    if v == "win":
        seq = _force_line(cells, binv, yinv) or []
        refs = []
    elif v == "trap":
        seq = _coop_line(cells, binv, yinv) or []
        refs = _refutations(cells, binv, yinv)
    else:
        seq = []
        refs = []
    if seq:
        first = seq[0].split(" ", 1)[1]
        pid, placement = first.split("@", 1)
        left = _replay_squares(cells, binv, yinv, seq)
    else:
        pid, placement = "", ""
        left = sq_left(binv)
    return {
        "board_id": bid,
        "status": v,
        "piece_id": pid,
        "placement": placement,
        "squares_left": left,
        "sequence": seq,
        "refutations": refs,
        "coop_fill": coop,
    }
