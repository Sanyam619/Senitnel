"""Round classification plus threat / refutation helpers."""
from __future__ import annotations

from board_hunt.op_b import (
    classify,
    coop_freedom_after,
    find_forcing_sequence,
    find_winning_first_moves,
    read_board,
    refutation_reply,
    threat_moves,
)

__all__ = [
    "build_fort_row",
    "build_trap_freedom",
    "build_trap_refs",
    "build_win_row",
    "classify",
    "read_board",
]


def build_trap_refs(state):
    refs = []
    for tm in threat_moves(state):
        reply = refutation_reply(state, tm)
        if reply is None:
            continue
        refs.append({"move": tm, "reply": reply})
    return sorted(refs, key=lambda x: x["move"])


def build_win_row(state):
    keys = find_winning_first_moves(state)
    key = min(keys) if keys else ""
    seq_info = find_forcing_sequence(state)
    if seq_info is None:
        # Immediate single-move fallback.
        for mv in keys:
            nxt = state.clone()
            nxt.to_move = "white"
            nxt.apply(mv)
            if nxt.pinned():
                return mv, [mv], nxt.freedom()
        return key, [], state.freedom()
    seq, freedom = seq_info
    first = seq[0] if seq else key
    return first, seq, freedom


def build_trap_freedom(state):
    return coop_freedom_after(state)


def build_fort_row(state):
    return state.freedom()
