"""Round-file reading plus threat / refutation classification."""
from __future__ import annotations

from board_hunt.op_b import (
    all_cells,
    black_linked,
    coop_fillable,
    solve,
)


def read_board(path):
    black, white, rows, in_board = set(), set(), [], False
    with open(path) as fh:
        for line in fh:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if t == "board:":
                in_board = True
                continue
            if in_board:
                rows.append(t)
    n = len(rows)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "B":
                black.add((c, r))
            elif ch == "W":
                white.add((c, r))
    return frozenset(black), frozenset(white), n


def immediate_completions(black, white, n):
    occ = set(black) | set(white)
    out = []
    for d in all_cells(n):
        if d in occ:
            continue
        if black_linked(frozenset(black) | {d}, n):
            out.append(d)
    return out


def threat_cells(black, white, n):
    occ = set(black) | set(white)
    out = []
    for c in all_cells(n):
        if c in occ:
            continue
        nb = frozenset(black) | {c}
        if black_linked(nb, n):
            continue
        if immediate_completions(nb, white, n):
            out.append(c)
    return out


def refutation_for(black, white, c, n):
    nb = frozenset(black) | {c}
    for w in all_cells(n):
        if w == c or w in (set(black) | set(white)):
            continue
        nw = frozenset(white) | {w}
        if not immediate_completions(nb, nw, n):
            return w
    return None


def classify(black, white, n):
    if black_linked(black, n):
        return "degenerate"
    if not coop_fillable(black, white, n):
        return "fort"
    if solve(black, white, "b", n):
        return "win"
    return "trap"
