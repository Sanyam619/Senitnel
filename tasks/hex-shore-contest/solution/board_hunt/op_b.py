"""Hex shore-chain helpers for the booklet search.

Black builds a stone chain from the north shore (row 0) to the south shore
(row N-1). White builds an east-west blockade from the left edge (col 0) to
the right edge (col N-1). Stones stay on the board, so a filled Hex board
always holds exactly one finished shore chain, and the force search stops
once a shore chain is complete.
"""
from __future__ import annotations

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def neighbors(c, r, n):
    for dc, dr in DIRS:
        nc, nr = c + dc, r + dr
        if 0 <= nc < n and 0 <= nr < n:
            yield nc, nr


def cell_name(c, r):
    return f"{chr(ord('a') + c)}{r + 1}"


def parse_cell(name):
    return ord(name[0]) - ord("a"), int(name[1:]) - 1


def all_cells(n):
    return [(c, r) for r in range(n) for c in range(n)]


def black_linked(black, n):
    stack = [(c, 0) for c in range(n) if (c, 0) in black]
    seen = set(stack)
    while stack:
        c, r = stack.pop()
        if r == n - 1:
            return True
        for nb in neighbors(c, r, n):
            if nb in black and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def coop_fillable(black, white, n):
    stack = [(c, 0) for c in range(n) if (c, 0) not in white]
    seen = set(stack)
    while stack:
        c, r = stack.pop()
        if r == n - 1:
            return True
        for nb in neighbors(c, r, n):
            if nb not in white and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def solve(black, white, side, n):
    """True iff Black can force the vertical link from this state."""
    memo = {}

    def rec(bl, wh, turn):
        if black_linked(bl, n):
            return True
        key = (bl, wh, turn)
        if key in memo:
            return memo[key]
        occ = bl | wh
        moves = [m for m in all_cells(n) if m not in occ]
        if not moves:
            memo[key] = black_linked(bl, n)
            return memo[key]
        if turn == "b":
            res = any(rec(bl | {m}, wh, "w") for m in moves)
        else:
            res = all(rec(bl, wh | {m}, "b") for m in moves)
        memo[key] = res
        return res

    return rec(frozenset(black), frozenset(white), side)


def winning_moves(black, white, n):
    occ = set(black) | set(white)
    out = []
    for m in all_cells(n):
        if m in occ:
            continue
        nb = frozenset(black) | {m}
        if black_linked(nb, n) or solve(nb, white, "w", n):
            out.append(m)
    return out
