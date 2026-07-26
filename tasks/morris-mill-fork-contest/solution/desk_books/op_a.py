"""Round classification plus threat / refutation helpers."""
from __future__ import annotations

from board_hunt.op_b import (
    classify,
    coop_mill,
    find_forcing_line,
    parse_board_file,
    refutation_reply,
    threat_moves,
)

__all__ = [
    "build_fort_row",
    "build_trap_row",
    "build_win_row",
    "classify",
    "read_board",
]


def read_board(path):
    return parse_board_file(path)


def build_win_row(state):
    line = find_forcing_line(state)
    if line is None:
        return "", [], [], 0
    seq, rems, mill_in, key = line
    return key, seq, rems, mill_in


def build_trap_row(state):
    _ok, _seq, _rems, mill_in, _key = coop_mill(state)
    refs = []
    for tm in threat_moves(state):
        reply = refutation_reply(state, tm)
        if reply is None:
            continue
        refs.append({"move": tm, "reply": reply})
    refs.sort(key=lambda x: x["move"])
    return mill_in, refs


def build_fort_row(_state):
    return 0
