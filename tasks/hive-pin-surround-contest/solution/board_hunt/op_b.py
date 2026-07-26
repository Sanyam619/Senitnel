"""Hive pin/surround search helpers for the booklet."""
from __future__ import annotations

from collections import deque
from copy import deepcopy

DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
# Success = Black queen fully surrounded (classic Hive). A soft pin that
# leaves one escape hex does not count.
PIN_FLOOR = 0
ANT_FREEDOM_FLOOR = 2
SCHEMA_TAG = "hive-pin-v1"


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def neighbors(cell):
    return [add(cell, d) for d in DIRS]


def parse_cell(s):
    q, r = s.split(",")
    return int(q), int(r)


def cell_str(q, r):
    return f"{q},{r}"


def move_token(pid, q, r):
    return f"{pid}>{cell_str(q, r)}"


def parse_move(tok):
    pid, dest = tok.split(">")
    return pid, parse_cell(dest)


def fingerprint(st):
    return (
        frozenset((pid, p["q"], p["r"], p["h"]) for pid, p in st.pieces.items()),
        st.moves_left,
    )


class State:
    __slots__ = ("moves_left", "pieces", "to_move")

    def __init__(self, pieces, moves_left, to_move="white"):
        self.pieces = pieces
        self.moves_left = moves_left
        self.to_move = to_move

    def clone(self):
        return State(deepcopy(self.pieces), self.moves_left, self.to_move)

    def at(self, cell):
        found = []
        for pid, p in self.pieces.items():
            if (p["q"], p["r"]) == cell:
                found.append((p["h"], pid, p))
        found.sort()
        return found

    def occupied(self):
        return {(p["q"], p["r"]) for p in self.pieces.values()}

    def occupied_without(self, pid):
        return {
            (p["q"], p["r"])
            for qid, p in self.pieces.items()
            if qid != pid
        }

    def queen(self, color):
        for pid, p in self.pieces.items():
            if p["color"] == color and p["kind"] == "Q":
                return pid, p
        return None, None

    def freedom(self, color="black"):
        _pid, q = self.queen(color)
        if q is None:
            return 0
        cell = (q["q"], q["r"])
        occ = self.occupied()
        return sum(1 for n in neighbors(cell) if n not in occ)

    def pinned(self):
        return self.freedom("black") <= PIN_FLOOR

    def connected(self, cells):
        if not cells:
            return True
        start = next(iter(cells))
        seen = {start}
        q = deque([start])
        while q:
            cur = q.popleft()
            for n in neighbors(cur):
                if n in cells and n not in seen:
                    seen.add(n)
                    q.append(n)
        return len(seen) == len(cells)

    def can_leave(self, pid):
        p = self.pieces[pid]
        cell = (p["q"], p["r"])
        stack = self.at(cell)
        if not stack or stack[-1][1] != pid:
            return False
        if len(stack) > 1:
            return True
        return self.connected(self.occupied_without(pid))

    def piece_freedom(self, pid):
        p = self.pieces[pid]
        if p["h"] > 0:
            return 6
        cell = (p["q"], p["r"])
        occ = self.occupied()
        return sum(1 for n in neighbors(cell) if n not in occ)

    def gate_ok(self, occ, a, b):
        common = set(neighbors(a)) & set(neighbors(b))
        if len(common) != 2:
            return False
        return any(c not in occ for c in common)

    def simulate_ok(self, pid, dest):
        if not self.can_leave(pid):
            return False
        cells = set()
        for qid, pp in self.pieces.items():
            if qid == pid:
                cells.add(dest)
            else:
                cells.add((pp["q"], pp["r"]))
        return self.connected(cells)

    def queen_dests(self, pid):
        if self.piece_freedom(pid) < 1 or not self.can_leave(pid):
            return []
        p = self.pieces[pid]
        start = (p["q"], p["r"])
        occ = self.occupied()
        out = []
        for nxt in neighbors(start):
            if nxt in occ:
                continue
            if not self.gate_ok(occ, start, nxt):
                continue
            if self.simulate_ok(pid, nxt):
                out.append(nxt)
        return out

    def beetle_dests(self, pid):
        if not self.can_leave(pid):
            return []
        p = self.pieces[pid]
        start = (p["q"], p["r"])
        return [n for n in neighbors(start) if self.simulate_ok(pid, n)]

    def grasshopper_dests(self, pid):
        if not self.can_leave(pid):
            return []
        p = self.pieces[pid]
        start = (p["q"], p["r"])
        occ = self.occupied()
        out = []
        for d in DIRS:
            cur = add(start, d)
            if cur not in occ:
                continue
            while cur in occ:
                cur = add(cur, d)
            if self.simulate_ok(pid, cur):
                out.append(cur)
        return out

    def slide_dests(self, pid, exact_steps=None, min_freedom=1):
        if self.piece_freedom(pid) < min_freedom or not self.can_leave(pid):
            return []
        p = self.pieces[pid]
        start = (p["q"], p["r"])
        rest = self.occupied_without(pid)
        if not rest:
            return []

        def touches(cell):
            return any(n in rest for n in neighbors(cell))

        # BFS on empty cells glued to the remaining hive
        best = {}
        q = deque([(start, 0)])
        seen_depth = {start: 0}
        while q:
            cur, dist = q.popleft()
            if exact_steps is not None and dist == exact_steps and cur != start:
                if cur not in rest and touches(cur):
                    best[cur] = dist
                continue
            if (
                exact_steps is None
                and dist > 0
                and cur != start
                and cur not in rest
                and touches(cur)
            ):
                best[cur] = dist
            if exact_steps is not None and dist >= exact_steps:
                continue
            limit = 20 if exact_steps is None else exact_steps
            if dist >= limit:
                continue
            for nxt in neighbors(cur):
                if nxt in rest:
                    continue
                if nxt != start and not touches(nxt):
                    continue
                if not self.gate_ok(rest, cur, nxt):
                    continue
                nd = dist + 1
                if exact_steps is None:
                    if nxt in seen_depth and seen_depth[nxt] <= nd:
                        continue
                    seen_depth[nxt] = nd
                    q.append((nxt, nd))
                else:
                    key = (nxt, nd)
                    if key in seen_depth:
                        continue
                    seen_depth[key] = nd
                    q.append((nxt, nd))
        return [d for d in best if self.simulate_ok(pid, d)]

    def legal_moves(self, color):
        moves = []
        for pid, p in self.pieces.items():
            if p["color"] != color:
                continue
            stack = self.at((p["q"], p["r"]))
            if not stack or stack[-1][1] != pid:
                continue
            kind = p["kind"]
            if kind == "Q":
                dests = self.queen_dests(pid)
            elif kind == "B":
                dests = self.beetle_dests(pid)
            elif kind == "G":
                dests = self.grasshopper_dests(pid)
            elif kind == "A":
                dests = self.slide_dests(pid, exact_steps=None, min_freedom=ANT_FREEDOM_FLOOR)
            elif kind == "S":
                dests = self.slide_dests(pid, exact_steps=3, min_freedom=1)
            else:
                dests = []
            for d in dests:
                moves.append(move_token(pid, *d))
        return sorted(set(moves))

    def apply(self, tok):
        pid, dest = parse_move(tok)
        p = self.pieces[pid]
        stack = [x for x in self.at(dest) if x[1] != pid]
        new_h = 0 if not stack else stack[-1][2]["h"] + 1
        # Flatten height if leaving a stack onto empty / recompute
        p["q"], p["r"], p["h"] = dest[0], dest[1], new_h
        if p["color"] == "white":
            self.moves_left -= 1
        self.to_move = "black" if self.to_move == "white" else "white"
        return self


def read_board(path):
    pieces = {}
    moves_left = 0
    to_move = "white"
    in_pieces = False
    with open(path) as fh:
        for line in fh:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if t == "pieces:":
                in_pieces = True
                continue
            if in_pieces:
                parts = t.split()
                pid, qs, rs, hs = parts[0], parts[1], parts[2], parts[3]
                color = "white" if pid.startswith("W") else "black"
                kind = pid.split("-")[1][0]
                pieces[pid] = {
                    "color": color,
                    "kind": kind,
                    "q": int(qs),
                    "r": int(rs),
                    "h": int(hs),
                }
                continue
            if ":" not in t:
                continue
            k, v = t.split(":", 1)
            k, v = k.strip(), v.strip()
            if k == "moves_left":
                moves_left = int(v)
            elif k == "to_move":
                to_move = v.lower()
    return State(pieces, moves_left, to_move)


def coop_pinable(state):
    memo = {}

    def rec(st):
        if st.pinned():
            return True
        if st.moves_left <= 0:
            return False
        key = fingerprint(st)
        if key in memo:
            return memo[key]
        for mv in st.legal_moves("white"):
            nxt = st.clone()
            nxt.to_move = "white"
            nxt.apply(mv)
            nxt.to_move = "white"
            if rec(nxt):
                memo[key] = True
                return True
        memo[key] = False
        return False

    return rec(state.clone())


def coop_sequence(state):
    """Shortest White-only move line reaching the pin floor, or None."""

    def rec(st, seq):
        if st.pinned():
            return seq, st.freedom()
        if st.moves_left <= 0:
            return None
        for mv in st.legal_moves("white"):
            nxt = st.clone()
            nxt.to_move = "white"
            nxt.apply(mv)
            got = rec(nxt, seq + [mv])
            if got is not None:
                return got
        return None

    return rec(state.clone(), [])


def coop_freedom_after(state):
    got = coop_sequence(state)
    if got is None:
        return state.freedom()
    return got[1]


def force_win_from(state, white_to_move):
    memo = {}

    def rec(st, wtm):
        if st.pinned():
            return True
        key = (*fingerprint(st), wtm)
        if key in memo:
            return memo[key]
        if wtm:
            if st.moves_left <= 0:
                memo[key] = False
                return False
            opts = st.legal_moves("white")
            if not opts:
                memo[key] = False
                return False
            for mv in opts:
                nxt = st.clone()
                nxt.to_move = "white"
                nxt.apply(mv)
                if nxt.pinned() or rec(nxt, False):
                    memo[key] = True
                    return True
            memo[key] = False
            return False
        opts = st.legal_moves("black")
        if not opts:
            memo[key] = rec(st, True)
            return memo[key]
        for mv in opts:
            nxt = st.clone()
            nxt.to_move = "black"
            nxt.apply(mv)
            if not rec(nxt, True):
                memo[key] = False
                return False
        memo[key] = True
        return True

    return rec(state.clone(), white_to_move)


def force_win(state):
    return force_win_from(state, True)


def classify(state):
    if force_win(state):
        return "win"
    if coop_pinable(state):
        return "trap"
    return "fort"


def find_winning_first_moves(state):
    """First White moves that keep a forced surround against fighting Black."""
    out = []
    for mv in state.legal_moves("white"):
        nxt = state.clone()
        nxt.to_move = "white"
        nxt.apply(mv)
        if nxt.pinned():
            out.append(mv)
            continue
        if force_win_from(nxt, False):
            out.append(mv)
    return sorted(set(out))


def find_forcing_sequence(state):
    """One short forcing line of move tokens; queen freedom after it."""

    def rec(st, wtm, seq):
        if st.pinned():
            return seq, st.freedom()
        if wtm:
            if st.moves_left <= 0:
                return None
            for mv in st.legal_moves("white"):
                nxt = st.clone()
                nxt.to_move = "white"
                nxt.apply(mv)
                if nxt.pinned():
                    return seq + [mv], nxt.freedom()
                if not force_win_from(nxt, False):
                    continue
                got = rec(nxt, False, seq + [mv])
                if got is not None:
                    return got
            return None
        opts = st.legal_moves("black")
        if not opts:
            return rec(st, True, seq)
        for mv in opts:
            nxt = st.clone()
            nxt.to_move = "black"
            nxt.apply(mv)
            got = rec(nxt, True, seq + [mv])
            if got is not None:
                return got
        return None

    return rec(state.clone(), True, [])


def threat_moves(state):
    if state.moves_left < 2:
        return []
    out = []
    for m1 in state.legal_moves("white"):
        mid = state.clone()
        mid.to_move = "white"
        mid.apply(m1)
        if mid.pinned():
            continue
        mid.to_move = "white"
        hit = False
        for m2 in mid.legal_moves("white"):
            end = mid.clone()
            end.to_move = "white"
            end.apply(m2)
            if end.pinned():
                hit = True
                break
        if hit:
            out.append(m1)
    return out


def refutation_reply(state, threat):
    mid = state.clone()
    mid.to_move = "white"
    mid.apply(threat)
    for reply in mid.legal_moves("black"):
        after = mid.clone()
        after.to_move = "black"
        after.apply(reply)
        can_pin = False
        for m2 in after.legal_moves("white"):
            end = after.clone()
            end.to_move = "white"
            end.apply(m2)
            if end.pinned():
                can_pin = True
                break
        if not can_pin:
            return reply
    return None


def write_board(path, round_id, moves_left, pieces, to_move="white"):
    lines = [
        f"round_id: {round_id}",
        f"to_move: {to_move}",
        f"moves_left: {moves_left}",
        "pieces:",
    ]
    for pid in sorted(pieces):
        p = pieces[pid]
        lines.append(f"{pid} {p['q']} {p['r']} {p['h']}")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
