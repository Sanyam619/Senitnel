"""Tak midgame engine helpers for road search."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass

N = 5
FILES = "abcde"
CARRY_LIMIT = 5
ROAD_FLOOR = 5
DIRS = {">": (1, 0), "<": (-1, 0), "+": (0, 1), "-": (0, -1)}
DIR_OF = {(1, 0): ">", (-1, 0): "<", (0, 1): "+", (0, -1): "-"}

# Piece alphabet (bottom→top in stack strings).
# w/W/C = white flat / standing / cap
# b/B/K = black flat / standing / cap


def cell_name(f: int, r: int) -> str:
    return f"{FILES[f]}{r}"


def parse_cell(name: str) -> tuple[int, int]:
    return FILES.index(name[0]), int(name[1:])


def is_cap(ch: str) -> bool:
    return ch in ("C", "K")


def is_standing(ch: str) -> bool:
    return ch in ("W", "B")


def is_flat(ch: str) -> bool:
    return ch in ("w", "b")


def color_of(ch: str) -> str:
    return "w" if ch in ("w", "W", "C") else "b"


def road_stone(top: str, who: str) -> bool:
    """Only flats and caps of `who` count; standings never do."""
    if who == "w":
        return top in ("w", "C")
    return top in ("b", "K")


@dataclass
class State:
    stacks: list[list[str]]  # stacks[f][r-1] bottom→top
    flats_w: int
    flats_b: int
    caps_w: int
    caps_b: int
    to_move: str  # 'w' or 'b'

    def clone(self) -> State:
        return State(
            deepcopy(self.stacks),
            self.flats_w,
            self.flats_b,
            self.caps_w,
            self.caps_b,
            self.to_move,
        )

    def stack_at(self, f: int, r: int) -> list[str]:
        return self.stacks[f][r - 1]

    def top(self, f: int, r: int) -> str | None:
        s = self.stack_at(f, r)
        return s[-1] if s else None

    def empty(self, f: int, r: int) -> bool:
        return not self.stack_at(f, r)


def empty_state(flats_w=10, flats_b=10, caps_w=1, caps_b=1, to_move="w") -> State:
    return State(
        [[[] for _ in range(N)] for _ in range(N)],
        flats_w,
        flats_b,
        caps_w,
        caps_b,
        to_move,
    )


def white_road_len(st: State) -> int | None:
    """Shortest White N–S road length, or None if no road."""
    starts = []
    for f in range(N):
        top = st.top(f, N)
        if top and road_stone(top, "w"):
            starts.append((f, N))
    if not starts:
        return None
    q = deque()
    dist = {}
    for s in starts:
        dist[s] = 1
        q.append(s)
    best = None
    while q:
        f, r = q.popleft()
        d = dist[(f, r)]
        if r == 1:
            best = d if best is None else min(best, d)
            continue
        for df, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nf, nr = f + df, r + dr
            if not (0 <= nf < N and 1 <= nr <= N):
                continue
            top = st.top(nf, nr)
            if not top or not road_stone(top, "w"):
                continue
            if (nf, nr) in dist:
                continue
            dist[(nf, nr)] = d + 1
            q.append((nf, nr))
    return best


def has_white_road(st: State) -> bool:
    ln = white_road_len(st)
    return ln is not None and ln >= ROAD_FLOOR


def place_ok(st: State, kind: str, f: int, r: int) -> bool:
    if not (0 <= f < N and 1 <= r <= N):
        return False
    if not st.empty(f, r):
        return False
    who = st.to_move
    if kind == "F":
        return (st.flats_w if who == "w" else st.flats_b) > 0
    if kind == "S":
        return (st.flats_w if who == "w" else st.flats_b) > 0
    if kind == "C":
        return (st.caps_w if who == "w" else st.caps_b) > 0
    return False


def apply_place(st: State, kind: str, f: int, r: int) -> State:
    ns = st.clone()
    who = ns.to_move
    if kind == "F":
        piece = "w" if who == "w" else "b"
        if who == "w":
            ns.flats_w -= 1
        else:
            ns.flats_b -= 1
    elif kind == "S":
        piece = "W" if who == "w" else "B"
        if who == "w":
            ns.flats_w -= 1
        else:
            ns.flats_b -= 1
    else:
        piece = "C" if who == "w" else "K"
        if who == "w":
            ns.caps_w -= 1
        else:
            ns.caps_b -= 1
    ns.stack_at(f, r).append(piece)
    ns.to_move = "b" if who == "w" else "w"
    return ns


def controlled_by(st: State, f: int, r: int, who: str) -> bool:
    top = st.top(f, r)
    if not top:
        return False
    return color_of(top) == who


def slide_destinations(st: State, f: int, r: int, carry: int):
    """Yield (dir_char, path_cells, drop_counts) for legal single-step slides."""
    stack = st.stack_at(f, r)
    if not stack or carry < 1 or carry > min(len(stack), CARRY_LIMIT):
        return
    who = st.to_move
    if color_of(stack[-1]) != who:
        return
    taken = stack[-carry:]
    for (df, dr), dch in DIR_OF.items():
        nf, nr = f + df, r + dr
        if not (0 <= nf < N and 1 <= nr <= N):
            continue
        dest = st.stack_at(nf, nr)
        if dest:
            top = dest[-1]
            if is_cap(top):
                continue
            if is_standing(top) and not (carry == 1 and is_cap(taken[0])):
                continue
        yield dch, [(nf, nr)], [carry]


def apply_slide(st: State, f: int, r: int, dch: str, drops: list[int]) -> State:
    ns = st.clone()
    carry = sum(drops)
    stack = ns.stack_at(f, r)
    taken = stack[-carry:]
    del stack[-carry:]
    df, dr = DIRS[dch]
    cf, cr = f, r
    idx = 0
    for drop in drops:
        cf += df
        cr += dr
        chunk = taken[idx : idx + drop]
        idx += drop
        dest = ns.stack_at(cf, cr)
        if dest and is_standing(dest[-1]):
            # Flatten: standing becomes flat of same color.
            wall = dest.pop()
            dest.append(wall.lower() if wall in ("W", "B") else wall)
        dest.extend(chunk)
    ns.to_move = "b" if st.to_move == "w" else "w"
    return ns


def move_token_place(kind: str, f: int, r: int) -> str:
    return f"{kind}:{cell_name(f, r)}"


def move_token_slide(f: int, r: int, dch: str, carry: int) -> str:
    # Single-step whole-carry drop: e.g. 2a3>2
    return f"{carry}{cell_name(f, r)}{dch}{carry}"


def parse_move(tok: str):
    tok = tok.strip()
    if ":" in tok and tok[0] in "FSC":
        kind, cell = tok.split(":", 1)
        return ("place", kind, parse_cell(cell))
    # slide: <carry><cell><dir><drop...>  booklet form NxyD N
    # e.g. 1a3>1 or 2b2+2
    i = 0
    while i < len(tok) and tok[i].isdigit():
        i += 1
    carry = int(tok[:i])
    cell = tok[i : i + 2]
    dch = tok[i + 2]
    drops_s = tok[i + 3 :]
    drops = [int(ch) for ch in drops_s] if drops_s else [carry]
    if sum(drops) != carry:
        # compact form NcellD N means one drop of N
        drops = [int(drops_s)] if drops_s.isdigit() else [carry]
    return ("slide", carry, parse_cell(cell), dch, drops)


def apply_token(st: State, tok: str) -> State | None:
    try:
        parsed = parse_move(tok)
    except (ValueError, IndexError, KeyError):
        return None
    if parsed[0] == "place":
        _, kind, (f, r) = parsed
        if not place_ok(st, kind, f, r):
            return None
        return apply_place(st, kind, f, r)
    _, carry, (f, r), dch, drops = parsed
    if sum(drops) != carry or carry > CARRY_LIMIT:
        return None
    legal = False
    for ch, _path, dps in slide_destinations(st, f, r, carry):
        if ch == dch and dps == drops:
            legal = True
            break
    if not legal and len(drops) == 1 and drops[0] == carry:
        for ch, _path, dps in slide_destinations(st, f, r, carry):
            if ch == dch:
                legal = True
                drops = dps
                break
    if not legal:
        return None
    return apply_slide(st, f, r, dch, drops)


def legal_moves(st: State, *, booklet: bool = True) -> list[str]:
    """Legal tokens. Booklet mode: White F/S/C + slides; Black flat-only replies."""
    out = []
    who = st.to_move
    if who == "b" and booklet:
        kinds = ("F",)
    elif who == "w" and booklet:
        kinds = ("F", "S", "C")
    else:
        kinds = ("F", "S", "C")
    for kind in kinds:
        for f in range(N):
            for r in range(1, N + 1):
                if place_ok(st, kind, f, r):
                    out.append(move_token_place(kind, f, r))
    if who == "b" and booklet:
        return out
    for f in range(N):
        for r in range(1, N + 1):
            if not controlled_by(st, f, r, who):
                continue
            h = len(st.stack_at(f, r))
            for carry in range(1, min(h, CARRY_LIMIT) + 1):
                for dch, path, drops in slide_destinations(st, f, r, carry):
                    out.append(move_token_slide(f, r, dch, carry))
    return out


def white_candidate_moves(st: State) -> list[str]:
    """Every legal White placement or slide in the booklet dialect."""
    cur = st.clone()
    cur.to_move = "w"
    return legal_moves(cur)


def black_candidate_moves(st: State) -> list[str]:
    cur = st.clone()
    cur.to_move = "b"
    return legal_moves(cur)


def coop_roadable(st: State, depth_left: int = 4) -> bool:
    """White can finish a road if Black never moves (White keeps turn)."""
    if has_white_road(st):
        return True
    if depth_left <= 0:
        return False
    cur = st.clone()
    cur.to_move = "w"
    for mv in white_candidate_moves(cur):
        nxt = apply_token(cur, mv)
        if nxt is None:
            continue
        nxt.to_move = "w"
        if coop_roadable(nxt, depth_left - 1):
            return True
    return False


def finishing_moves(st: State) -> list[str]:
    """Legal White moves that complete a road immediately."""
    cur = st.clone()
    cur.to_move = "w"
    out = []
    for mv in white_candidate_moves(cur):
        nxt = apply_token(cur, mv)
        if nxt is not None and has_white_road(nxt):
            out.append(mv)
    return out


def forcing_replies(st: State, first_move: str) -> dict[str, list[str]] | None:
    """Map every Black flat reply to White finishes, or None if refutable."""
    cur = st.clone()
    cur.to_move = "w"
    after = apply_token(cur, first_move)
    if after is None:
        return None
    if has_white_road(after):
        return {}
    replies = black_candidate_moves(after)
    if not replies:
        finishes = finishing_moves(after)
        return {"pass": finishes} if finishes else None
    reply_map = {}
    for reply in replies:
        answered = apply_token(after, reply)
        if answered is None:
            continue
        finishes = finishing_moves(answered)
        if not finishes:
            return None
        reply_map[reply] = finishes
    return reply_map


def force_win(st: State, white_to_move: bool = True, depth: int = 3, memo=None) -> bool:
    """White finishes now or after every legal Black flat reply."""
    del depth, memo, white_to_move
    if has_white_road(st):
        return True
    for mv in white_candidate_moves(st):
        if forcing_replies(st, mv) is not None:
            return True
    return False


def winning_first_moves(st: State) -> list[str]:
    return [
        mv
        for mv in white_candidate_moves(st)
        if forcing_replies(st, mv) is not None
    ]


def find_forcing_sequence(st: State) -> list[str]:
    cur = st.clone()
    cur.to_move = "w"
    for mv in winning_first_moves(st):
        nxt = apply_token(cur, mv)
        if nxt is not None and has_white_road(nxt):
            return [mv]
        replies = forcing_replies(st, mv)
        if replies:
            reply = min(replies)
            if reply == "pass":
                return [mv, min(replies[reply])]
            return [mv, reply, min(replies[reply])]
    return []


def threat_moves(st: State) -> list[str]:
    """First White moves that do not finish, but leave a one-move finish if Black passes."""
    cur = st.clone()
    cur.to_move = "w"
    out = []
    for mv in white_candidate_moves(cur):
        nxt = apply_token(cur, mv)
        if nxt is None or has_white_road(nxt):
            continue
        if finishing_moves(nxt):
            out.append(mv)
    return out


def refutation_reply(st: State, threat: str) -> str | None:
    cur = st.clone()
    cur.to_move = "w"
    after = apply_token(cur, threat)
    if after is None:
        return None
    after.to_move = "b"
    for reply in black_candidate_moves(after):
        n2 = apply_token(after, reply)
        if n2 is None:
            continue
        if not finishing_moves(n2):
            return reply
    return None


def classify(st: State) -> str:
    if force_win(st):
        return "win"
    if coop_roadable(st, depth_left=4):
        return "trap"
    return "fort"


def board_rows(st: State) -> list[str]:
    """North-first rows; stacks as contiguous piece glyphs, '.' for empty."""
    rows = []
    for rank in range(N, 0, -1):
        cells = []
        for f in range(N):
            s = st.stack_at(f, rank)
            cells.append("".join(s) if s else ".")
        rows.append(" ".join(cells))
    return rows


def write_board(path: str, st: State, round_id: int) -> None:
    lines = [
        f"round_id: {round_id}",
        "to_move: white",
        f"flats_w: {st.flats_w}",
        f"flats_b: {st.flats_b}",
        f"caps_w: {st.caps_w}",
        f"caps_b: {st.caps_b}",
        "board:",
    ]
    lines.extend(board_rows(st))
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def read_board(path: str) -> State:
    flats_w = flats_b = 10
    caps_w = caps_b = 1
    to_move = "w"
    rows: list[str] = []
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
            if k == "flats_w":
                flats_w = int(v)
            elif k == "flats_b":
                flats_b = int(v)
            elif k == "caps_w":
                caps_w = int(v)
            elif k == "caps_b":
                caps_b = int(v)
            elif k == "to_move":
                to_move = "w" if v.lower().startswith("w") else "b"
    st = empty_state(flats_w, flats_b, caps_w, caps_b, to_move)
    assert len(rows) == N
    for i, row in enumerate(rows):
        rank = N - i
        parts = row.split()
        assert len(parts) == N, row
        for f, cell in enumerate(parts):
            if cell == ".":
                continue
            # stack pieces separated by '.' e.g. w.b.W
            pieces = cell.split(".") if "." in cell else list(cell)
            # If no dots and multi-char, treat each char as a piece.
            if "." not in cell:
                pieces = list(cell)
            st.stacks[f][rank - 1] = pieces
    return st


def set_stack(st: State, cell: str, pieces: str) -> None:
    f, r = parse_cell(cell)
    st.stacks[f][r - 1] = list(pieces)


