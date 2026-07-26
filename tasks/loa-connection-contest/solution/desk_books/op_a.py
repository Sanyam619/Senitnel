"""Round-sheet reading, verdicts, and the certificates each verdict needs."""
from __future__ import annotations

from line_walk.op_b import (
    after,
    answer_to,
    forcing_moves,
    gathering_moves,
    group_count,
    move_name,
    moves_for,
    one_group,
    pressing_moves,
    unopposed_plan,
)

UNOPPOSED_BUDGET = 5


def read_board(path):
    rows = []
    in_board = False
    with open(path) as fh:
        for line in fh:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            if text == "board:":
                in_board = True
                continue
            if in_board:
                rows.append(text)
    size = len(rows)
    mine = frozenset(
        (r, c)
        for r, row in enumerate(rows)
        for c, ch in enumerate(row)
        if ch == "B"
    )
    theirs = frozenset(
        (r, c)
        for r, row in enumerate(rows)
        for c, ch in enumerate(row)
        if ch == "W"
    )
    return mine, theirs, size


def classify(mine, theirs, size):
    if forcing_moves(mine, theirs, size):
        return "win"
    if unopposed_plan(mine, theirs, size, UNOPPOSED_BUDGET) is not None:
        return "trap"
    return "fort"


def forcing_line(mine, theirs, size):
    """One legal line starting from a forcing move, sides alternating."""
    for move in forcing_moves(mine, theirs, size):
        nm, nt = after(mine, theirs, move)
        if one_group(nm):
            return [move_name(*move)]
        answers = sorted(moves_for(nt, nm, size))
        if not answers:
            finish = min(gathering_moves(nm, nt, size))
            return [move_name(*move), move_name(*finish)]
        answer = answers[0]
        at, am = after(nt, nm, answer)
        finish = min(gathering_moves(am, at, size))
        return [move_name(*move), move_name(*answer), move_name(*finish)]
    return []


def replay(mine, theirs, size, tokens):
    """Replay alternating tokens (mover first); returns the ending position."""
    from line_walk.op_b import move_of

    cur_mine, cur_theirs = frozenset(mine), frozenset(theirs)
    mover = True
    for token in tokens:
        move = move_of(token)
        if mover:
            legal = moves_for(cur_mine, cur_theirs, size)
            assert move in legal, f"illegal step {token}"
            cur_mine, cur_theirs = after(cur_mine, cur_theirs, move)
        else:
            legal = moves_for(cur_theirs, cur_mine, size)
            assert move in legal, f"illegal step {token}"
            cur_theirs, cur_mine = after(cur_theirs, cur_mine, move)
        mover = not mover
    return cur_mine, cur_theirs


def build_trap_refs(mine, theirs, size):
    rows = []
    for press in pressing_moves(mine, theirs, size):
        answer = answer_to(mine, theirs, size, press)
        assert answer is not None, f"no answer for {move_name(*press)}"
        rows.append({"move": move_name(*press), "reply": move_name(*answer)})
    return sorted(rows, key=lambda row: row["move"])


def scored_components(mine, theirs, size, verdict):
    """Group count belonging to the position the verdict describes."""
    if verdict == "win":
        line = forcing_line(mine, theirs, size)
        end_mine, _end_theirs = replay(mine, theirs, size, line)
        return group_count(end_mine)
    if verdict == "trap":
        plan = unopposed_plan(mine, theirs, size, UNOPPOSED_BUDGET)
        assert plan is not None
        cur_mine, cur_theirs = frozenset(mine), frozenset(theirs)
        for move in plan:
            cur_mine, cur_theirs = after(cur_mine, cur_theirs, move)
        return group_count(cur_mine)
    return group_count(mine)
