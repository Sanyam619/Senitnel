"""Santorini summit search for the tournament desk."""
from __future__ import annotations

from pathlib import Path

FILES = "abcde"
RANKS = "12345"
SQUARES = [f + r for r in RANKS for f in FILES]
IDX = {sq: i for i, sq in enumerate(SQUARES)}
DIRS = [(df, dr) for df in (-1, 0, 1) for dr in (-1, 0, 1) if not (df == 0 and dr == 0)]


def nbrs(sq: str) -> list[str]:
    f, r = FILES.index(sq[0]), int(sq[1]) - 1
    out = []
    for df, dr in DIRS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 5 and 0 <= nr < 5:
            out.append(FILES[nf] + str(nr + 1))
    return out


class State:
    __slots__ = ("budget", "h", "occ", "to_move")

    def __init__(self, h, first, second, to_move="first", budget=2):
        self.h = list(h)  # 0..3 or 4=dome
        self.occ = {sq: None for sq in SQUARES}
        for sq in first:
            self.occ[sq] = "F"
        for sq in second:
            self.occ[sq] = "S"
        self.to_move = to_move
        self.budget = int(budget)

    def clone(self):
        n = State.__new__(State)
        n.h = self.h[:]
        n.occ = dict(self.occ)
        n.to_move = self.to_move
        n.budget = self.budget
        return n

    def workers(self, side: str) -> list[str]:
        ch = "F" if side == "first" else "S"
        return [sq for sq in SQUARES if self.occ[sq] == ch]

    def height(self, sq: str) -> int:
        return self.h[IDX[sq]]

    def is_dome(self, sq: str) -> bool:
        return self.h[IDX[sq]] >= 4

    def legal_moves(self, side: str | None = None) -> list[str]:
        side = side or self.to_move
        ch = "F" if side == "first" else "S"
        toks = []
        for fr in self.workers(side):
            hf = self.height(fr)
            for to in nbrs(fr):
                if self.occ[to] is not None or self.is_dome(to):
                    continue
                ht = self.height(to)
                if ht - hf > 1:
                    continue
                # Winning ascent: move onto 3, no build.
                if ht == 3:
                    toks.append(f"{ch}:{fr}-{to}")
                    continue
                for b in nbrs(to):
                    # After leaving fr, fr is empty and buildable when adjacent.
                    if b != fr and self.occ[b] is not None:
                        continue
                    if self.is_dome(b):
                        continue
                    toks.append(f"{ch}:{fr}-{to}:{b}")
        return sorted(set(toks))

    def apply(self, tok: str) -> State:
        side = "first" if tok[0] == "F" else "second"
        assert side == self.to_move, (tok, self.to_move)
        body = tok[2:]
        if ":" in body.split("-", 1)[-1] if False else True:
            pass
        parts = body.split(":")
        if len(parts) == 1:
            fr, to = parts[0].split("-")
            build = None
        else:
            fr_to, build = parts[0], parts[1]
            fr, to = fr_to.split("-")
        nxt = self.clone()
        assert nxt.occ[fr] == ("F" if side == "first" else "S")
        nxt.occ[fr] = None
        nxt.occ[to] = "F" if side == "first" else "S"
        ht = nxt.height(to)
        if ht == 3:
            assert build is None
            # win — turn ends; budget spent for first
            if side == "first":
                nxt.budget -= 1
            nxt.to_move = "second" if side == "first" else "first"
            return nxt
        assert build is not None
        bi = IDX[build]
        assert nxt.occ[build] is None or build == fr  # fr already cleared
        assert nxt.h[bi] < 4
        nxt.h[bi] += 1
        if nxt.h[bi] > 3:
            nxt.h[bi] = 4  # dome after building on 3
        if side == "first":
            nxt.budget -= 1
        nxt.to_move = "second" if side == "first" else "first"
        return nxt

    def first_summited(self, tok: str) -> bool:
        if not tok.startswith("F:"):
            return False
        body = tok[2:]
        if ":" in body:
            fr_to = body.split(":")[0]
        else:
            fr_to = body
        _fr, to = fr_to.split("-")
        return self.height(to) == 3

    def dump(self) -> str:
        rows = []
        for r in range(5, 0, -1):
            cells = []
            for f in FILES:
                sq = f + str(r)
                h = self.height(sq)
                hs = "D" if h >= 4 else str(h)
                w = self.occ[sq] or "."
                cells.append(hs + w)
            rows.append(" ".join(cells))
        return "\n".join(rows)


def parse_token_summit_delta(st: State, tok: str) -> int:
    body = tok[2:]
    fr_to = body.split(":")[0]
    fr, to = fr_to.split("-")
    return st.height(to) - st.height(fr)


def coop_summit(st: State, budget: int | None = None) -> tuple[bool, list[str], int]:
    """First-only plan; Second passes (to_move stays/skips). Returns (ok, line, height_delta)."""
    budget = st.budget if budget is None else budget
    # BFS on first-only turns
    from collections import deque

    start = st.clone()
    start.to_move = "first"
    start.budget = budget
    q = deque([(start, [])])
    seen = set()
    while q:
        cur, line = q.popleft()
        if cur.budget < 0:
            continue
        key = (tuple(cur.h), tuple(cur.occ[s] for s in SQUARES), cur.budget)
        if key in seen:
            continue
        seen.add(key)
        if cur.to_move != "first":
            # skip second
            cur = cur.clone()
            cur.to_move = "first"
        if cur.budget <= 0 and not line:
            continue
        moves = sorted(cur.legal_moves("first"), key=lambda t: (0 if cur.first_summited(t) else 1, t))
        for tok in moves:
            if cur.first_summited(tok):
                delta = parse_token_summit_delta(cur, tok)
                return True, line + [tok], delta
            if cur.budget <= 1:
                continue
            nxt = cur.apply(tok)
            # after apply, to_move is second — force back to first without spending
            nxt.to_move = "first"
            # budget already decremented
            q.append((nxt, line + [tok]))
    return False, [], 0


def force_win(st: State, budget: int | None = None) -> tuple[bool, list[str], int]:
    budget = st.budget if budget is None else budget
    memo: dict = {}

    def first_can(cur: State) -> tuple[bool, list[str], int]:
        if cur.budget <= 0:
            return False, [], 0
        key = (tuple(cur.h), tuple(cur.occ[s] for s in SQUARES), cur.budget, "F")
        if key in memo:
            return memo[key]
        moves = sorted(cur.legal_moves("first"), key=lambda t: (0 if cur.first_summited(t) else 1, t))
        for tok in moves:
            if cur.first_summited(tok):
                delta = parse_token_summit_delta(cur, tok)
                memo[key] = (True, [tok], delta)
                return memo[key]
            nxt = cur.apply(tok)
            # Second replies
            ok_all, reply_line, delta = second_fails_to_stop(nxt)
            if ok_all:
                memo[key] = (True, [tok] + reply_line, delta)
                return memo[key]
        memo[key] = (False, [], 0)
        return memo[key]

    def second_fails_to_stop(cur: State) -> tuple[bool, list[str], int]:
        # After First moved; Second to move. First still wins after EVERY Second reply.
        key = (tuple(cur.h), tuple(cur.occ[s] for s in SQUARES), cur.budget, "S")
        if key in memo:
            return memo[key]
        replies = cur.legal_moves("second")
        if not replies:
            # Second passes — First continues
            nxt = cur.clone()
            nxt.to_move = "first"
            ok, line, delta = first_can(nxt)
            memo[key] = (ok, line, delta)
            return memo[key]
        # Need one concrete line for the card: pick any reply and show continuation
        # But ALL replies must leave First able to force.
        witness = None
        for rep in replies:
            nxt = cur.apply(rep)
            ok, line, delta = first_can(nxt)
            if not ok:
                memo[key] = (False, [], 0)
                return memo[key]
            if witness is None:
                witness = ([rep] + line, delta)
        memo[key] = (True, witness[0], witness[1])
        return memo[key]

    return first_can(st.clone())


def threats(st: State) -> list[str]:
    """Non-summit first turns that leave a coop summit on the next First turn."""
    out = []
    for tok in st.legal_moves("first"):
        if st.first_summited(tok):
            continue
        nxt = st.apply(tok)
        nxt.to_move = "first"  # Second passes
        # budget already -1
        ok, _line, _d = coop_summit(nxt, budget=1)
        # also allow remaining budget
        if not ok:
            ok, _line, _d = coop_summit(nxt, budget=max(1, nxt.budget))
        if ok:
            # stricter: exists second First move that summits immediately
            immediate = False
            for t2 in nxt.legal_moves("first"):
                if nxt.first_summited(t2):
                    immediate = True
                    break
            if immediate:
                out.append(tok)
    return out


def classify(st: State) -> dict:
    fw, fline, fd = force_win(st)
    cw, cline, cd = coop_summit(st)
    if fw:
        status = "win"
        coop = True
        return {
            "status": status,
            "coop_summit": coop,
            "sequence": fline,
            "height_delta": fd,
            "key_move": fline[0] if fline else "",
            "refutations": [],
            "threats": [],
        }
    if cw:
        th = threats(st)
        refs = []
        for th_tok in th:
            # find a Second reply that kills immediate follow-up summit
            mid = st.apply(th_tok)
            found = None
            for rep in mid.legal_moves("second"):
                after = mid.apply(rep)
                after.to_move = "first"
                can = any(after.first_summited(t) for t in after.legal_moves("first"))
                if not can:
                    found = rep
                    break
            if found is None:
                # if no refutation exists, this "threat" is actually still forcing-ish;
                # still list threat but skip — for traps Second should be able to answer
                continue
            refs.append({"move": th_tok, "reply": found})
        return {
            "status": "trap",
            "coop_summit": True,
            "sequence": [],
            "height_delta": cd,
            "key_move": "",
            "refutations": refs,
            "threats": th,
            "coop_line": cline,
        }
    return {
        "status": "fort",
        "coop_summit": False,
        "sequence": [],
        "height_delta": 0,
        "key_move": "",
        "refutations": [],
        "threats": [],
    }


def make(h5, first, second, budget=2):
    """h5[0] is rank 5 (top), h5[4] is rank 1 (bottom); each row a..e."""
    flat = [0] * 25
    for ri, row in enumerate(h5):
        rank = 5 - ri
        for ci, v in enumerate(row):
            sq = FILES[ci] + str(rank)
            flat[IDX[sq]] = 4 if v in (4, "D") else int(v)
    return State(flat, first, second, "first", budget)


def write_puzzle(path, board_id, st, note=""):
    lines = [
        f"board_id: {board_id}",
        "to_move: first",
        f"budget: {st.budget}",
        "heights:",
    ]
    for r in range(5, 0, -1):
        row = []
        for f in FILES:
            h = st.height(f + str(r))
            row.append("D" if h >= 4 else str(h))
        lines.append(" ".join(row))
    lines.append("first: " + " ".join(st.workers("first")))
    lines.append("second: " + " ".join(st.workers("second")))
    if note:
        lines.append(f"# {note}")
    path.write_text("\n".join(lines) + "\n")



def load_puzzle(path):
    path = str(path)
    budget = 2
    height_rows = []
    first = []
    second = []
    in_h = False
    board_id = None
    with open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("board_id:"):
                board_id = line.split(":", 1)[1].strip()
            elif line.startswith("budget:"):
                budget = int(line.split(":", 1)[1].strip())
            elif line == "heights:":
                in_h = True
            elif line.startswith("first:"):
                in_h = False
                first = line.split(":", 1)[1].split()
            elif line.startswith("second:"):
                in_h = False
                second = line.split(":", 1)[1].split()
            elif in_h:
                height_rows.append([4 if c == "D" else int(c) for c in line.split()])
    st = make(height_rows, first, second, budget=budget)
    return board_id or Path(path).stem, st


def classify_round(st):
    return classify(st)


def row_from_class(board_id, c):
    return {
        "board_id": board_id,
        "status": c["status"],
        "coop_summit": bool(c["coop_summit"]),
        "key_move": c.get("key_move") or "",
        "sequence": list(c.get("sequence") or []),
        "refutations": list(c.get("refutations") or []),
    }
