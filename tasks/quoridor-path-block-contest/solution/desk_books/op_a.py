"""Round-file reading plus threat / refutation helpers."""
from __future__ import annotations

from board_hunt.op_b import (
    PATH_FLOOR,
    cell_name,
    coop_blockable,
    coop_sequence,
    find_forcing_sequence,
    force_win,
    place_wall,
    refutation_reply,
    threat_walls,
    white_path,
    winning_first_walls,
)


def read_board(path):
    black = white = None
    walls = []
    walls_left = 0
    rows = []
    in_board = False
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
                continue
            if ":" not in t:
                continue
            k, v = t.split(":", 1)
            k, v = k.strip(), v.strip()
            if k == "walls_left":
                walls_left = int(v)
            elif k == "walls":
                walls = v.split() if v else []
    # rows[0] is rank 5 (north), rows[-1] is rank 1 (south)
    for i, row in enumerate(rows):
        rank = 5 - i
        for f, ch in enumerate(row):
            if ch == "B":
                black = (f, rank)
            elif ch == "W":
                white = (f, rank)
    return {
        "black": black,
        "white": white,
        "walls": frozenset(walls),
        "walls_left": walls_left,
    }


def classify(state):
    b, w = state["black"], state["white"]
    walls, left = state["walls"], state["walls_left"]
    if force_win(b, w, walls, left, True):
        return "win"
    if coop_blockable(b, w, walls, left):
        return "trap"
    return "fort"


def build_trap_refs(state):
    b, w = state["black"], state["white"]
    walls, left = state["walls"], state["walls_left"]
    refs = []
    for tw in threat_walls(b, w, walls, left):
        reply = refutation_reply(b, w, walls, left, tw)
        if reply is None:
            continue
        refs.append({"move": tw, "reply": cell_name(*reply)})
    return sorted(refs, key=lambda x: x["move"])


def build_win_row(state):
    b, w = state["black"], state["white"]
    walls, left = state["walls"], state["walls_left"]
    keys = winning_first_walls(b, w, walls, left)
    key = sorted(keys)[0] if keys else ""
    seq_info = find_forcing_sequence(b, w, walls, left)
    if seq_info is None:
        # Immediate single wall fallback
        for wid in keys:
            nw = place_wall(walls, wid)
            wp = white_path(w, b, nw)
            if wp is not None and wp >= PATH_FLOOR:
                return wid, [f"wall:{wid}"], wp
        return key, [], white_path(w, b, walls) or 0
    seq, plen = seq_info
    # key_wall is first wall token
    first = ""
    for tok in seq:
        if tok.startswith("wall:"):
            first = tok.split(":", 1)[1]
            break
    if not first and key:
        first = key
    return first, seq, plen


def build_fort_path(state):
    return white_path(state["white"], state["black"], state["walls"])


def build_trap_path(state):
    got = coop_sequence(
        state["black"], state["white"], state["walls"], state["walls_left"]
    )
    if got is None:
        return white_path(state["white"], state["black"], state["walls"])
    return got[1]
