"""Patchwork economy round engine.

A round is a two-player patch-market game. The First player (Red) and the
opponent (Blue) share one time track and one market of patches. The player whose
time token is further back takes the next turn (Red on a tie). A turn is either
an advance (jump just past the other token, banking one button per space) or a
take (pay a patch's button cost, lay its polyomino on the quilt without overlap,
push the time token forward by the patch's time cost). Crossing an income spot
banks buttons equal to the printed income of the patches already laid down.

Red's closing score is banked buttons minus two per still-empty quilt cell. A
round is a ``win`` when Red can force the score floor against every Blue line, a
``trap`` when Red only reaches the floor if Blue keeps advancing, and a ``fort``
when the floor is out of reach even against an idle Blue.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache


@dataclass(frozen=True)
class Patch:
    pid: str
    time: int
    cost: int
    income: int
    cells: tuple[tuple[int, int], ...]

    @property
    def size(self) -> int:
        return len(self.cells)


@dataclass(frozen=True)
class Board:
    board_id: str
    rows: int
    cols: int
    blocked: frozenset[int]
    track: int
    income: tuple[int, ...]
    floor: int
    red_start: int
    blue_start: int
    patches: tuple[Patch, ...]

    @property
    def area(self) -> int:
        return self.rows * self.cols

    def patch(self, pid: str) -> Patch:
        for p in self.patches:
            if p.pid == pid:
                return p
        raise KeyError(pid)


# state = (rt, rb, red_taken, bt, bb, blue_taken)
State = tuple[int, int, frozenset[str], int, int, frozenset[str]]


def parse_board(text: str) -> Board:
    board_id = ""
    rows = cols = track = floor = red_start = blue_start = 0
    blocked: set[int] = set()
    income: tuple[int, ...] = ()
    patches: list[Patch] = []
    in_market = False
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if in_market:
            head, _, shape = stripped.partition(":")
            fields = head.split()
            pid, t, c, inc = fields[0], int(fields[1]), int(fields[2]), int(fields[3])
            cells = _shape_cells(shape.strip())
            patches.append(Patch(pid, t, c, inc, cells))
            continue
        if stripped.startswith("board_id:"):
            board_id = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("quilt:"):
            rc = stripped.split(":", 1)[1].strip().lower().split("x")
            rows, cols = int(rc[0]), int(rc[1])
        elif stripped.startswith("blocked:"):
            body = stripped.split(":", 1)[1].strip()
            for tok in body.split(","):
                tok = tok.strip()
                if tok:
                    blocked.add(_cell_of(tok, cols))
        elif stripped.startswith("time_track:"):
            track = int(stripped.split(":", 1)[1].strip())
        elif stripped.startswith("income:"):
            body = stripped.split(":", 1)[1].strip()
            income = tuple(int(x) for x in body.split(",") if x.strip())
        elif stripped.startswith("floor:"):
            floor = int(stripped.split(":", 1)[1].strip())
        elif stripped.startswith("red_start:"):
            red_start = int(stripped.split(":", 1)[1].strip())
        elif stripped.startswith("blue_start:"):
            blue_start = int(stripped.split(":", 1)[1].strip())
        elif stripped == "market:":
            in_market = True
    return Board(
        board_id=board_id,
        rows=rows,
        cols=cols,
        blocked=frozenset(blocked),
        track=track,
        income=income,
        floor=floor,
        red_start=red_start,
        blue_start=blue_start,
        patches=tuple(patches),
    )


def _cell_of(token: str, cols: int) -> int:
    token = token.strip().lower()
    r = int(token[token.index("r") + 1 : token.index("c")])
    c = int(token[token.index("c") + 1 :])
    return r * cols + c


def _shape_cells(shape: str) -> tuple[tuple[int, int], ...]:
    pts: list[tuple[int, int]] = []
    for r, row in enumerate(shape.split("/")):
        for c, ch in enumerate(row):
            if ch == "X":
                pts.append((r, c))
    minr = min(p[0] for p in pts)
    minc = min(p[1] for p in pts)
    return tuple(sorted((r - minr, c - minc) for r, c in pts))


# ---------------------------------------------------------------------------
# packing (geometry feasibility)
# ---------------------------------------------------------------------------


def _pack(board: Board, taken: frozenset[str]) -> dict[str, int] | None:
    """Return {pid: anchor_cell} packing all taken patches, or None if infeasible."""
    order = sorted(taken, key=lambda p: (-board.patch(p).size, p))
    occupied = set(board.blocked)
    placement: dict[str, int] = {}

    def place(idx: int) -> bool:
        if idx == len(order):
            return True
        patch = board.patch(order[idx])
        for anchor in range(board.area):
            ar, ac = divmod(anchor, board.cols)
            cells = []
            ok = True
            for dr, dc in patch.cells:
                rr, cc = ar + dr, ac + dc
                if not (0 <= rr < board.rows and 0 <= cc < board.cols):
                    ok = False
                    break
                idxc = rr * board.cols + cc
                if idxc in occupied:
                    ok = False
                    break
                cells.append(idxc)
            if not ok:
                continue
            occupied.update(cells)
            placement[order[idx]] = anchor
            if place(idx + 1):
                return True
            occupied.difference_update(cells)
            del placement[order[idx]]
        return False

    if place(0):
        return dict(placement)
    return None


_fit_cache: dict[tuple[str, frozenset[str]], bool] = {}


def fit(board: Board, taken: frozenset[str]) -> bool:
    key = (board.board_id, taken)
    hit = _fit_cache.get(key)
    if hit is None:
        hit = _pack(board, taken) is not None
        _fit_cache[key] = hit
    return hit


# ---------------------------------------------------------------------------
# game mechanics
# ---------------------------------------------------------------------------


def initial(board: Board) -> State:
    return (0, board.red_start, frozenset(), 0, board.blue_start, frozenset())


def _income_rate(board: Board, taken: frozenset[str]) -> int:
    return sum(board.patch(p).income for p in taken)


def _crossed(board: Board, t0: int, t1: int, rate: int) -> int:
    return rate * sum(1 for s in board.income if t0 < s <= t1)


def market(board: Board, st: State) -> frozenset[str]:
    _, _, red_taken, _, _, blue_taken = st
    return frozenset(p.pid for p in board.patches) - red_taken - blue_taken


def to_move(board: Board, st: State) -> str | None:
    rt, _, _, bt, _, _ = st
    if rt == board.track and bt == board.track:
        return None
    if rt < bt:
        return "R"
    if bt < rt:
        return "B"
    return "R"


def red_moves(board: Board, st: State) -> list[tuple]:
    _, rb, red_taken, _, _, _ = st
    moves: list[tuple] = [("R", "adv")]
    for pid in sorted(market(board, st)):
        patch = board.patch(pid)
        if patch.cost <= rb and fit(board, red_taken | {pid}):
            moves.append(("R", "take", pid))
    return moves


def blue_moves(board: Board, st: State) -> list[tuple]:
    _, _, _, _, bb, _ = st
    moves: list[tuple] = [("B", "adv")]
    for pid in sorted(market(board, st)):
        patch = board.patch(pid)
        if patch.cost <= bb:
            moves.append(("B", "take", pid))
    return moves


def legal_moves(board: Board, st: State) -> list[tuple]:
    side = to_move(board, st)
    if side == "R":
        return red_moves(board, st)
    if side == "B":
        return blue_moves(board, st)
    return []


def apply_move(board: Board, st: State, move: tuple) -> State:
    rt, rb, red_taken, bt, bb, blue_taken = st
    side = move[0]
    if side == "R":
        if move[1] == "adv":
            new_rt = min(board.track, bt + 1)
            rate = _income_rate(board, red_taken)
            gain = (new_rt - rt) + _crossed(board, rt, new_rt, rate)
            return (new_rt, rb + gain, red_taken, bt, bb, blue_taken)
        pid = move[2]
        patch = board.patch(pid)
        new_taken = red_taken | {pid}
        rate = _income_rate(board, new_taken)
        new_rt = min(board.track, rt + patch.time)
        new_rb = rb - patch.cost + _crossed(board, rt, new_rt, rate)
        return (new_rt, new_rb, new_taken, bt, bb, blue_taken)
    if move[1] == "adv":
        new_bt = min(board.track, rt + 1)
        rate = _income_rate(board, blue_taken)
        gain = (new_bt - bt) + _crossed(board, bt, new_bt, rate)
        return (rt, rb, red_taken, new_bt, bb + gain, blue_taken)
    pid = move[2]
    patch = board.patch(pid)
    new_taken = blue_taken | {pid}
    rate = _income_rate(board, new_taken)
    new_bt = min(board.track, bt + patch.time)
    new_bb = bb - patch.cost + _crossed(board, bt, new_bt, rate)
    return (rt, rb, red_taken, new_bt, new_bb, new_taken)


def terminal(board: Board, st: State) -> bool:
    return to_move(board, st) is None


def red_score(board: Board, st: State) -> int:
    _, rb, red_taken, _, _, _ = st
    covered = sum(board.patch(p).size for p in red_taken)
    free = board.area - len(board.blocked) - covered
    return rb - 2 * free


# ---------------------------------------------------------------------------
# search: forced / cooperative reachability
# ---------------------------------------------------------------------------


def _solver(board: Board):
    @cache
    def forced(st: State) -> bool:
        if terminal(board, st):
            return red_score(board, st) >= board.floor
        side = to_move(board, st)
        children = (apply_move(board, st, m) for m in legal_moves(board, st))
        if side == "R":
            return any(forced(c) for c in children)
        return all(forced(c) for c in children)

    @cache
    def coop(st: State) -> bool:
        if terminal(board, st):
            return red_score(board, st) >= board.floor
        side = to_move(board, st)
        if side == "R":
            return any(coop(apply_move(board, st, m)) for m in red_moves(board, st))
        return coop(apply_move(board, st, ("B", "adv")))

    return forced, coop


def verdict(board: Board) -> str:
    forced, coop = _solver(board)
    st0 = initial(board)
    if forced(st0):
        return "win"
    if coop(st0):
        return "trap"
    return "fort"


def candidate_first_takes(board: Board) -> list[str]:
    st0 = initial(board)
    return [m[2] for m in red_moves(board, st0) if m[0] == "R" and m[1] == "take"]


# ---------------------------------------------------------------------------
# move <-> string
# ---------------------------------------------------------------------------


def move_to_str(board: Board, st: State, move: tuple, placement: dict[str, int]) -> str:
    side_word = "red" if move[0] == "R" else "blue"
    if move[1] == "adv":
        return f"{side_word} advance"
    pid = move[2]
    if move[0] == "R":
        anchor = placement[pid]
        ar, ac = divmod(anchor, board.cols)
        return f"{side_word} take {pid} @ r{ar}c{ac}"
    return f"{side_word} take {pid}"


def parse_step(step: str) -> tuple:
    parts = step.strip().split()
    if len(parts) < 2:
        raise ValueError(f"bad step {step!r}")
    side = {"red": "R", "blue": "B"}.get(parts[0])
    if side is None:
        raise ValueError(f"bad side {step!r}")
    if parts[1] == "advance":
        return (side, "adv")
    if parts[1] == "take":
        pid = parts[2]
        return (side, "take", pid)
    raise ValueError(f"bad action {step!r}")


# ---------------------------------------------------------------------------
# oracle line construction
# ---------------------------------------------------------------------------


def _emit_line(board: Board, moves: list[tuple]) -> list[str]:
    """Render a move list to card strings using one fixed packing of Red's takes.

    Every patch keeps a single anchor for the whole line, so replaying the line
    incrementally never produces overlaps.
    """
    final_taken = frozenset(m[2] for m in moves if m[0] == "R" and m[1] == "take")
    placement = _pack(board, final_taken) or {}
    st = initial(board)
    out: list[str] = []
    for move in moves:
        out.append(move_to_str(board, st, move, placement))
        st = apply_move(board, st, move)
    return out


def win_line(board: Board) -> list[tuple]:
    forced, _ = _solver(board)

    def walk(st: State) -> list[tuple]:
        if terminal(board, st):
            return []
        side = to_move(board, st)
        moves = legal_moves(board, st)
        if side == "R":
            for m in sorted(moves, key=lambda m: 0 if m[1] == "take" else 1):
                nxt = apply_move(board, st, m)
                if forced(nxt):
                    return [m] + walk(nxt)
            raise RuntimeError("win_line: no forcing move")
        # Blue: any legal move keeps the position forced; pick the one that
        # drags the line longest so the emitted line reaches a terminal state.
        best = max(moves, key=lambda m: 0 if m[1] == "adv" else 1)
        return [best] + walk(apply_move(board, st, best))

    return walk(initial(board))


def coop_line(board: Board) -> list[tuple]:
    _, coop = _solver(board)

    def walk(st: State) -> list[tuple] | None:
        if terminal(board, st):
            return [] if red_score(board, st) >= board.floor else None
        side = to_move(board, st)
        if side == "R":
            ordered = sorted(red_moves(board, st), key=lambda m: 0 if m[1] == "take" else 1)
            for m in ordered:
                nxt = apply_move(board, st, m)
                if coop(nxt):
                    rest = walk(nxt)
                    if rest is not None:
                        return [m] + rest
            return None
        nxt = apply_move(board, st, ("B", "adv"))
        rest = walk(nxt)
        return [("B", "adv")] + rest if rest is not None else None

    line = walk(initial(board))
    if line is None:
        raise RuntimeError("coop_line: no cooperative line")
    return line


def refutations(board: Board) -> list[dict[str, str]]:
    """For each takeable opening patch, a Blue reply that stops the floor."""
    forced, _ = _solver(board)
    out: list[dict[str, str]] = []
    for pid in candidate_first_takes(board):
        st1 = apply_move(board, initial(board), ("R", "take", pid))
        # Prefer an active denial (Blue takes a patch) over a bare advance when
        # one refutes; either is a valid refutation.
        options = sorted(blue_moves(board, st1), key=lambda m: 0 if m[1] == "take" else 1)
        reply = None
        for m in options:
            if not forced(apply_move(board, st1, m)):
                reply = "advance" if m[1] == "adv" else f"take {m[2]}"
                break
        if reply is None:
            raise RuntimeError(f"refutations: no reply for {pid}")
        out.append({"patch_id": pid, "reply": reply})
    return out


def build_round(board: Board) -> dict:
    status = verdict(board)
    if status == "fort":
        return {
            "board_id": board.board_id,
            "status": "fort",
            "patch_id": "",
            "time_cost": 0,
            "buttons": 0,
            "sequence": [],
            "refutations": [],
            "coop_fill": False,
        }
    moves = win_line(board) if status == "win" else coop_line(board)
    first_pid = next(m[2] for m in moves if m[0] == "R" and m[1] == "take")
    patch = board.patch(first_pid)
    return {
        "board_id": board.board_id,
        "status": status,
        "patch_id": first_pid,
        "time_cost": patch.time,
        "buttons": patch.income,
        "sequence": _emit_line(board, moves),
        "refutations": refutations(board) if status == "trap" else [],
        "coop_fill": True,
    }
