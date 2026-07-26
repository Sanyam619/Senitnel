"""Round-file reading plus threat / refutation helpers."""
from __future__ import annotations

from board_hunt.op_b import (
    apply_token,
    classify,
    coop_roadable,
    find_forcing_sequence,
    force_win,
    has_white_road,
    read_board,
    refutation_reply,
    threat_moves,
    white_road_len,
    winning_first_moves,
)


def build_trap_refs(state):
    refs = []
    for tw in threat_moves(state):
        reply = refutation_reply(state, tw)
        if reply is None:
            continue
        refs.append({"move": tw, "reply": reply})
    return sorted(refs, key=lambda x: (x["move"], x["reply"]))


def key_square_of(move: str) -> str:
    if ":" in move and move[0] in "FSC":
        return move.split(":", 1)[1]
    # slide: <carry><cell><dir>...
    i = 0
    while i < len(move) and move[i].isdigit():
        i += 1
    return move[i : i + 2]


def coop_road_len(state):
    """Road length after a cooperative White-only plan (or 0)."""
    from collections import deque

    from board_hunt.op_b import white_candidate_moves

    if has_white_road(state):
        return white_road_len(state) or 0

    q = deque([(state.clone(), 0)])
    seen: set[tuple] = set()

    def key_of(st):
        cells = tuple("".join(st.stacks[f][r]) for f in range(5) for r in range(5))
        return (cells, st.flats_w, st.caps_w)

    seen.add(key_of(state))
    while q:
        cur, depth = q.popleft()
        if has_white_road(cur):
            return white_road_len(cur) or 0
        if depth >= 4:
            continue
        cur = cur.clone()
        cur.to_move = "w"
        for mv in white_candidate_moves(cur):
            nxt = apply_token(cur, mv)
            if nxt is None:
                continue
            nxt.to_move = "w"
            k = key_of(nxt)
            if k in seen:
                continue
            seen.add(k)
            q.append((nxt, depth + 1))
    return 0


__all__ = [
    "apply_token",
    "build_trap_refs",
    "classify",
    "coop_road_len",
    "coop_roadable",
    "find_forcing_sequence",
    "force_win",
    "has_white_road",
    "key_square_of",
    "read_board",
    "threat_moves",
    "white_road_len",
    "winning_first_moves",
]
