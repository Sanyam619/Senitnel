"""Board search helpers for the connection booklet.

Pieces travel along a rank or a file only, exactly as many squares as there
are pieces of either colour standing on that whole line (the travelling
piece included). Friendly pieces may be passed over, enemy pieces may not,
an enemy piece on the destination is taken, and a friendly piece on the
destination is refused. A side holds the board when every one of its
surviving pieces sits in one eight-neighbour group.
"""
from __future__ import annotations

ADJ8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
STEPS = ((0, 1), (0, -1), (1, 0), (-1, 0))


def square_name(pos):
    r, c = pos
    return f"{chr(ord('a') + c)}{r + 1}"


def square_of(name):
    return (int(name[1:]) - 1, ord(name[0]) - ord("a"))


def move_name(src, dst):
    return f"{square_name(src)}-{square_name(dst)}"


def move_of(token):
    head, tail = token.split("-")
    return (square_of(head), square_of(tail))


def group_count(pieces):
    left = set(pieces)
    total = 0
    while left:
        total += 1
        stack = [left.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in ADJ8:
                nb = (r + dr, c + dc)
                if nb in left:
                    left.discard(nb)
                    stack.append(nb)
    return total


def one_group(pieces):
    return group_count(pieces) == 1


def moves_for(mine, theirs, size):
    """Every legal move for the side holding `mine`."""
    occupied = mine | theirs
    out = []
    for src in sorted(mine):
        r, c = src
        on_rank = sum(1 for cc in range(size) if (r, cc) in occupied)
        on_file = sum(1 for rr in range(size) if (rr, c) in occupied)
        for dr, dc in STEPS:
            reach = on_rank if dr == 0 else on_file
            tr, tc = r + dr * reach, c + dc * reach
            if not (0 <= tr < size and 0 <= tc < size):
                continue
            if (tr, tc) in mine:
                continue
            shut = False
            for step in range(1, reach):
                if (r + dr * step, c + dc * step) in theirs:
                    shut = True
                    break
            if shut:
                continue
            out.append((src, (tr, tc)))
    return out


def after(mine, theirs, move):
    src, dst = move
    return frozenset((set(mine) - {src}) | {dst}), frozenset(set(theirs) - {dst})


def gathering_moves(mine, theirs, size):
    """Moves for `mine` that leave that side in a single group."""
    out = []
    for move in moves_for(mine, theirs, size):
        nm, _nt = after(mine, theirs, move)
        if one_group(nm):
            out.append(move)
    return out


def forcing_moves(mine, theirs, size):
    """First moves that settle the round inside two turns of `mine`."""
    out = []
    for move in moves_for(mine, theirs, size):
        nm, nt = after(mine, theirs, move)
        if one_group(nm):
            out.append(move)
            continue
        answers = moves_for(nt, nm, size)
        if not answers:
            if gathering_moves(nm, nt, size):
                out.append(move)
            continue
        held = True
        for answer in answers:
            at, am = after(nt, nm, answer)
            if not gathering_moves(am, at, size):
                held = False
                break
        if held:
            out.append(move)
    return out


def unopposed_plan(mine, theirs, size, budget):
    """A run of moves for `mine` alone that ends in a single group."""
    tried = set()

    def walk(cur_mine, cur_theirs, left, trail):
        if one_group(cur_mine):
            return trail
        if left <= 0:
            return None
        key = (cur_mine, cur_theirs, left)
        if key in tried:
            return None
        tried.add(key)
        for move in moves_for(cur_mine, cur_theirs, size):
            nm, nt = after(cur_mine, cur_theirs, move)
            found = walk(nm, nt, left - 1, trail + [move])
            if found is not None:
                return found
        return None

    return walk(frozenset(mine), frozenset(theirs), budget, [])


def pressing_moves(mine, theirs, size):
    """First moves that do not gather but leave a one-move gather behind."""
    out = []
    for move in moves_for(mine, theirs, size):
        nm, nt = after(mine, theirs, move)
        if one_group(nm):
            continue
        if gathering_moves(nm, nt, size):
            out.append(move)
    return out


def answer_to(mine, theirs, size, press):
    """An enemy reply after `press` that kills the one-move gather."""
    nm, nt = after(mine, theirs, press)
    for answer in moves_for(nt, nm, size):
        at, am = after(nt, nm, answer)
        if not gathering_moves(am, at, size):
            return answer
    return None
