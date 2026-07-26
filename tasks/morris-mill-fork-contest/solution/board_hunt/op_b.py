"""Nine Men's Morris mill-fork core (authoring seed — not shipped in task)."""
from __future__ import annotations

from itertools import combinations

POINTS = (
    "a7", "d7", "g7",
    "b6", "d6", "f6",
    "c5", "d5", "e5",
    "a4", "b4", "c4", "e4", "f4", "g4",
    "c3", "d3", "e3",
    "b2", "d2", "f2",
    "a1", "d1", "g1",
)

ADJ = {
    "a7": ("d7", "a4"),
    "d7": ("a7", "g7", "d6"),
    "g7": ("d7", "g4"),
    "b6": ("d6", "b4"),
    "d6": ("d7", "b6", "f6", "d5"),
    "f6": ("d6", "f4"),
    "c5": ("d5", "c4"),
    "d5": ("d6", "c5", "e5"),
    "e5": ("d5", "e4"),
    "a4": ("a7", "b4", "a1"),
    "b4": ("b6", "a4", "c4", "b2"),
    "c4": ("c5", "b4", "c3"),
    "e4": ("e5", "f4", "e3"),
    "f4": ("f6", "e4", "g4", "f2"),
    "g4": ("g7", "f4", "g1"),
    "c3": ("c4", "d3"),
    "d3": ("c3", "e3", "d2"),
    "e3": ("e4", "d3"),
    "b2": ("b4", "d2"),
    "d2": ("d3", "b2", "f2", "d1"),
    "f2": ("f4", "d2"),
    "a1": ("a4", "d1"),
    "d1": ("a1", "g1", "d2"),
    "g1": ("g4", "d1"),
}

MILLS = (
    ("a7", "d7", "g7"),
    ("a1", "d1", "g1"),
    ("a7", "a4", "a1"),
    ("g7", "g4", "g1"),
    ("b6", "d6", "f6"),
    ("b2", "d2", "f2"),
    ("b6", "b4", "b2"),
    ("f6", "f4", "f2"),
    ("c5", "d5", "e5"),
    ("c3", "d3", "e3"),
    ("c5", "c4", "c3"),
    ("e5", "e4", "e3"),
    ("a4", "b4", "c4"),
    ("e4", "f4", "g4"),
    ("d7", "d6", "d5"),
    ("d3", "d2", "d1"),
)

MILL_FLOOR = 1
FLY_COUNT = 3
SCHEMA_TAG = "morris-mill-v1"


def _ch(side: str) -> str:
    return "W" if side == "white" else "B"


def _side(ch: str) -> str:
    return "white" if ch == "W" else "black"


class State:
    __slots__ = ("board", "moves_left", "pending_mills", "pending_remove", "to_move")

    def __init__(
        self,
        board,
        to_move="white",
        moves_left=3,
        pending_remove=None,
        pending_mills=0,
    ):
        self.board = {p: board.get(p) for p in POINTS}
        self.to_move = to_move
        self.moves_left = int(moves_left)
        self.pending_remove = pending_remove
        self.pending_mills = int(pending_mills)

    def clone(self):
        return State(
            dict(self.board),
            self.to_move,
            self.moves_left,
            self.pending_remove,
            self.pending_mills,
        )

    def fp(self):
        return (
            tuple(self.board[p] for p in POINTS),
            self.to_move,
            self.moves_left,
            self.pending_remove,
            self.pending_mills,
        )

    def count(self, side: str) -> int:
        c = _ch(side)
        return sum(1 for p in POINTS if self.board[p] == c)

    def flying(self, side: str) -> bool:
        return self.count(side) <= FLY_COUNT

    def occupied(self, side: str):
        c = _ch(side)
        return [p for p in POINTS if self.board[p] == c]

    def empty(self):
        return [p for p in POINTS if self.board[p] is None]

    def mills_at(self, point: str, side: str):
        c = _ch(side)
        return [m for m in MILLS if point in m and all(self.board[x] == c for x in m)]

    def in_mill(self, point: str) -> bool:
        v = self.board[point]
        if v is None:
            return False
        return bool(self.mills_at(point, _side(v)))

    def removable(self, victim: str):
        pts = self.occupied(victim)
        free = [p for p in pts if not self.in_mill(p)]
        return free if free else list(pts)

    def dests(self, fr: str, side: str):
        if self.board[fr] != _ch(side):
            return []
        if self.flying(side):
            return list(self.empty())
        return [d for d in ADJ[fr] if self.board[d] is None]

    def slides(self, side: str):
        return [(fr, to) for fr in self.occupied(side) for to in self.dests(fr, side)]


def move_token(fr: str, to: str, side: str) -> str:
    return f"{_ch(side)}:{fr}-{to}"


def parse_token(tok: str):
    if tok in ("B:pass", "W:pass", "pass"):
        return ("black" if tok.startswith("B") else "white"), "pass", "pass"
    ch, rest = tok.split(":", 1)
    fr, to = rest.split("-", 1)
    return _side(ch), fr, to


def _end_turn(st: State, side: str) -> State:
    nxt = st.clone()
    nxt.pending_remove = None
    nxt.pending_mills = 0
    if side == "white":
        nxt.moves_left -= 1
    nxt.to_move = "black" if side == "white" else "white"
    return nxt


def apply_slide(st: State, fr: str, to: str) -> tuple[State, int]:
    side = st.to_move
    assert st.pending_remove is None
    assert (fr, to) in st.slides(side)
    nxt = st.clone()
    nxt.board[fr] = None
    nxt.board[to] = _ch(side)
    mills = len(nxt.mills_at(to, side))
    if mills:
        nxt.pending_remove = side
        nxt.pending_mills = mills
        return nxt, mills
    return _end_turn(nxt, side), 0


def apply_remove(st: State, point: str) -> State:
    assert st.pending_remove is not None and st.pending_mills > 0
    side = st.pending_remove
    victim = "black" if side == "white" else "white"
    assert point in st.removable(victim)
    nxt = st.clone()
    nxt.board[point] = None
    nxt.pending_mills -= 1
    if nxt.pending_mills > 0:
        nxt.pending_remove = side
        return nxt
    return _end_turn(nxt, side)


def white_actions(st: State):
    """Yield (seq_tokens, removals, new_state, mills, key_point)."""
    assert st.to_move == "white" and st.pending_remove is None
    if st.moves_left <= 0:
        return
    for fr, to in st.slides("white"):
        mid, mills = apply_slide(st, fr, to)
        tok = move_token(fr, to, "white")
        if mills == 0:
            yield [tok], [], mid, 0, ""
            continue
        opts = mid.removable("black")
        if mills == 1:
            for pt in opts:
                yield [tok], [pt], apply_remove(mid, pt), 1, to
        else:
            for combo in combinations(sorted(opts), mills):
                cur = mid.clone()
                ok = True
                used = []
                for i, pt in enumerate(combo):
                    if pt not in cur.removable("black"):
                        ok = False
                        break
                    used.append(pt)
                    cur = apply_remove(cur, pt)
                if ok:
                    yield [tok], used, cur, mills, to


def black_actions(st: State):
    assert st.to_move == "black" and st.pending_remove is None
    slides = st.slides("black")
    if not slides:
        nxt = st.clone()
        nxt.to_move = "white"
        yield ["B:pass"], [], nxt, 0
        return
    for fr, to in slides:
        mid, mills = apply_slide(st, fr, to)
        tok = move_token(fr, to, "black")
        if mills == 0:
            yield [tok], [], mid, 0
            continue
        opts = mid.removable("white")
        if mills == 1:
            for pt in opts:
                yield [tok], [pt], apply_remove(mid, pt), mills
        else:
            for combo in combinations(sorted(opts), mills):
                cur = mid.clone()
                ok = True
                for pt in combo:
                    if pt not in cur.removable("white"):
                        ok = False
                        break
                    cur = apply_remove(cur, pt)
                if ok:
                    yield [tok], list(combo), cur, mills


_FORCE_CACHE: dict = {}
_COOP_CACHE: dict = {}


def clear_caches():
    _FORCE_CACHE.clear()
    _COOP_CACHE.clear()


def force_mill(st: State) -> bool:
    """White can force forming ≥ MILL_FLOOR mills against fighting Black."""

    def wplay(s: State) -> bool:
        key = ("w", s.fp())
        if key in _FORCE_CACHE:
            return _FORCE_CACHE[key]
        if s.moves_left <= 0:
            _FORCE_CACHE[key] = False
            return False
        for _toks, _rems, nxt, mills, _k in white_actions(s):
            if mills >= MILL_FLOOR:
                _FORCE_CACHE[key] = True
                return True
            if not bhold(nxt):
                _FORCE_CACHE[key] = True
                return True
        _FORCE_CACHE[key] = False
        return False

    def bhold(s: State) -> bool:
        """True if Black can still prevent a forced mill."""
        key = ("b", s.fp())
        if key in _FORCE_CACHE:
            return _FORCE_CACHE[key]
        if s.to_move != "black":
            val = not wplay(s)
            _FORCE_CACHE[key] = val
            return val
        holds = False
        for _toks, _rems, nxt, _m in black_actions(s):
            if not wplay(nxt):
                holds = True
                break
        _FORCE_CACHE[key] = holds
        return holds

    clear_caches()
    return wplay(st.clone())


def coop_mill(st: State):
    """Black always passes. Returns (ok, sequence, removals, mill_in, key_point)."""

    def dfs(s: State, seq, rems, acc, key):
        fk = (s.fp(), acc)
        if fk in _COOP_CACHE:
            return None
        _COOP_CACHE[fk] = True
        if acc >= MILL_FLOOR:
            return seq, rems, acc, key
        if s.moves_left <= 0 or s.to_move != "white":
            return None
        for toks, rem, nxt, mills, k in white_actions(s):
            nseq = seq + toks
            nrem = rems + rem
            nacc = acc + mills
            nkey = k if mills else key
            if nacc >= MILL_FLOOR:
                return nseq, nrem, nacc, nkey
            # black passes
            if nxt.to_move == "black":
                passed = nxt.clone()
                passed.to_move = "white"
                nxt = passed
            got = dfs(nxt, nseq, nrem, nacc, nkey)
            if got:
                return got
        return None

    _COOP_CACHE.clear()
    got = dfs(st.clone(), [], [], 0, "")
    if got is None:
        return False, [], [], 0, ""
    return True, got[0], got[1], got[2], got[3]


def classify(st: State) -> str:
    if force_mill(st):
        return "win"
    ok, *_ = coop_mill(st)
    if ok:
        return "trap"
    return "fort"


def threat_moves(st: State) -> list[str]:
    out = []
    for toks, _rem, nxt, mills, _k in white_actions(st):
        if mills >= MILL_FLOOR:
            continue
        tok = toks[0]
        cur = nxt.clone()
        if cur.to_move == "black":
            cur.to_move = "white"
        if cur.moves_left <= 0:
            continue
        for _t2, _r2, _n2, m2, _ in white_actions(cur):
            if m2 >= MILL_FLOOR:
                out.append(tok)
                break
    return sorted(set(out))


def refutation_reply(st: State, threat: str) -> str | None:
    match = None
    for toks, _rem, nxt, mills, _k in white_actions(st):
        if toks[0] == threat and mills < MILL_FLOOR:
            match = nxt
            break
    if match is None or match.to_move != "black":
        return None
    for btoks, _br, after, _m in black_actions(match):
        if after.to_move != "white":
            continue
        can = any(m >= MILL_FLOOR for _t, _r, _n, m, _ in white_actions(after))
        if not can:
            return btoks[0]
    return None


def find_forcing_line(st: State):
    if not force_mill(st):
        return None

    def build(s, seq, rems, acc, key):
        if acc >= MILL_FLOOR:
            return seq, rems, acc, key
        if s.to_move != "white" or s.moves_left <= 0:
            return None
        cands = []
        for toks, rem, nxt, mills, k in white_actions(s):
            nseq = seq + toks
            nrem = rems + rem
            nacc = acc + mills
            nkey = k if mills else key
            if nacc >= MILL_FLOOR:
                return nseq, nrem, nacc, nkey
            # preserves force against all black replies?
            if preserves(nxt):
                cands.append((toks[0], nxt, nseq, nrem, nacc, nkey))
        for _tok, nxt, nseq, nrem, nacc, nkey in sorted(cands, key=lambda x: x[0]):
            got = extend_black(nxt, nseq, nrem, nacc, nkey)
            if got:
                return got
        return None

    def preserves(s):
        if s.to_move != "black":
            return force_mill(s)
        for _t, _r, after, _m in black_actions(s):
            if not force_mill(after):
                return False
        return True

    def extend_black(s, seq, rems, acc, key):
        acts = list(black_actions(s))
        # concrete PV: lex-min black reply, then continue
        btoks, _br, after, _m = min(acts, key=lambda x: x[0][0])
        return build(after, seq + btoks, rems, acc, key)

    clear_caches()
    return build(st.clone(), [], [], 0, "")


def parse_board_file(path: str) -> State:
    meta = {}
    board = {p: None for p in POINTS}
    mode = None
    with open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line in ("board:", "white:", "black:"):
                mode = line[:-1]
                continue
            if mode is None and ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
                continue
            if mode == "board":
                for tok in line.split():
                    pt, ch = tok.split("=", 1)
                    board[pt] = None if ch in (".", "-") else ch
            elif mode in ("white", "black"):
                for pt in line.split():
                    board[pt] = "W" if mode == "white" else "B"
    return State(board, meta.get("to_move", "white"), int(meta.get("moves_left", "3")))
