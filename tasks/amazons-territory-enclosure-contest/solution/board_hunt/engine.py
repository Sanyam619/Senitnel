"""Amazons territory enclosure engine (5x5)."""
from __future__ import annotations

from functools import cache

N = 5
FILES = "abcde"
EMPTY, WHITE, BLACK, ARROW = 0, 1, 2, 3
DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
FLOOR = 2
BUDGET = 3


def name(i: int) -> str:
    return f"{FILES[i % N]}{i // N + 1}"


def spot(s: str) -> int:
    return (int(s[1]) - 1) * N + FILES.index(s[0])


def queen_rays(cells: tuple[int, ...], start: int) -> list[int]:
    out: list[int] = []
    sf, sr = start % N, start // N
    for df, dr in DIRS:
        f, r = sf + df, sr + dr
        while 0 <= f < N and 0 <= r < N:
            i = r * N + f
            if cells[i] != EMPTY:
                break
            out.append(i)
            f += df
            r += dr
    return out


def amazons(cells: tuple[int, ...], who: int) -> list[int]:
    return [i for i, v in enumerate(cells) if v == who]


def legal_turns(cells: tuple[int, ...], who: int) -> list[tuple[int, int, int]]:
    turns: list[tuple[int, int, int]] = []
    for src in amazons(cells, who):
        for dst in queen_rays(cells, src):
            mid = list(cells)
            mid[src] = EMPTY
            mid[dst] = who
            mid_t = tuple(mid)
            for arr in queen_rays(mid_t, dst):
                turns.append((src, dst, arr))
    return sorted(set(turns))


def apply_turn(cells: tuple[int, ...], turn: tuple[int, int, int], who: int) -> tuple[int, ...]:
    src, dst, arr = turn
    board = list(cells)
    if board[src] != who:
        raise ValueError("no amazon at src")
    board[src] = EMPTY
    if board[dst] != EMPTY:
        raise ValueError("dst blocked")
    board[dst] = who
    if board[arr] != EMPTY:
        raise ValueError("arrow blocked")
    board[arr] = ARROW
    return tuple(board)


def reachable(cells: tuple[int, ...], who: int) -> set[int]:
    frontier = list(amazons(cells, who))
    seen_pos = set(frontier)
    reached_empty: set[int] = set()
    while frontier:
        cur = frontier.pop()
        for nxt in queen_rays(cells, cur):
            if nxt not in seen_pos:
                seen_pos.add(nxt)
                reached_empty.add(nxt)
                frontier.append(nxt)
    return reached_empty


def territory(cells: tuple[int, ...]) -> tuple[int, int, int]:
    w = reachable(cells, WHITE)
    b = reachable(cells, BLACK)
    we = len(w - b)
    be = len(b - w)
    return we, be, we - be


def enclosed(cells: tuple[int, ...]) -> bool:
    return territory(cells)[2] >= FLOOR


def parse_board(text: str) -> tuple[int, ...]:
    rows: list[str] = []
    inb = False
    for line in text.splitlines():
        t = line.strip()
        if t == "board:":
            inb = True
            continue
        if inb and t:
            rows.append(t)
            if len(rows) == N:
                break
    cells = [EMPTY] * (N * N)
    for ri, row in enumerate(rows):
        rank = N - 1 - ri
        for f, ch in enumerate(row):
            cells[rank * N + f] = {".": EMPTY, "W": WHITE, "B": BLACK, "X": ARROW}[ch]
    return tuple(cells)


def fmt_move(turn: tuple[int, int, int]) -> str:
    a, b, c = turn
    return f"{name(a)}-{name(b)}/{name(c)}"


def parse_move(s: str) -> tuple[int, int, int]:
    left, arr = s.split("/")
    src, dst = left.split("-")
    return spot(src), spot(dst), spot(arr)


@cache
def can_force(cells: tuple[int, ...], stones: int) -> bool:
    if enclosed(cells):
        return True
    if stones <= 0:
        return False
    wt = legal_turns(cells, WHITE)
    if not wt:
        return enclosed(cells)
    for t in wt:
        after = apply_turn(cells, t, WHITE)
        if enclosed(after):
            return True
        if stones == 1:
            continue
        bt = legal_turns(after, BLACK)
        if not bt:
            if can_force(after, stones - 1):
                return True
            continue
        if all(can_force(apply_turn(after, r, BLACK), stones - 1) for r in bt):
            return True
    return False


@cache
def can_coop(cells: tuple[int, ...], stones: int) -> bool:
    if enclosed(cells):
        return True
    if stones <= 0:
        return False
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        if enclosed(after) or can_coop(after, stones - 1):
            return True
    return False


def verdict(cells: tuple[int, ...]) -> str:
    can_force.cache_clear()
    can_coop.cache_clear()
    if can_force(cells, BUDGET):
        return "win"
    if can_coop(cells, BUDGET):
        return "trap"
    return "fort"


def threats(cells: tuple[int, ...]) -> list[tuple[int, int, int]]:
    out = []
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        if enclosed(after):
            continue
        for t2 in legal_turns(after, WHITE):
            if enclosed(apply_turn(after, t2, WHITE)):
                out.append(t)
                break
    return out


def find_refutation(cells: tuple[int, ...], threat: tuple[int, int, int]):
    after = apply_turn(cells, threat, WHITE)
    for r in legal_turns(after, BLACK):
        held = apply_turn(after, r, BLACK)
        if not any(enclosed(apply_turn(held, t2, WHITE)) for t2 in legal_turns(held, WHITE)):
            return r
    return None


def forcing_first_moves(cells: tuple[int, ...]) -> list[tuple[int, int, int]]:
    out = []
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        if enclosed(after):
            out.append(t)
            continue
        bt = legal_turns(after, BLACK)
        if not bt:
            if can_force(after, BUDGET - 1):
                out.append(t)
        elif all(can_force(apply_turn(after, r, BLACK), BUDGET - 1) for r in bt):
            out.append(t)
    return out


def find_coop_line(cells: tuple[int, ...], stones: int = BUDGET) -> list[tuple[int, int, int]] | None:
    if enclosed(cells):
        return []
    if stones <= 0:
        return None
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        if enclosed(after):
            return [t]
        rest = find_coop_line(after, stones - 1)
        if rest is not None:
            return [t] + rest
    return None


def find_force_line(cells: tuple[int, ...], stones: int = BUDGET) -> list[str] | None:
    """Return alternating colour steps ending when the territory floor is met."""
    if enclosed(cells):
        return []
    if stones <= 0:
        return None
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        step_w = f"white {fmt_move(t)}"
        if enclosed(after):
            return [step_w]
        if stones == 1:
            continue
        bt = legal_turns(after, BLACK)
        if not bt:
            rest = find_force_line(after, stones - 1)
            if rest is not None:
                return [step_w] + rest
            continue
        if not all(can_force(apply_turn(after, r, BLACK), stones - 1) for r in bt):
            continue
        for r in bt:
            held = apply_turn(after, r, BLACK)
            step_b = f"black {fmt_move(r)}"
            if enclosed(held):
                return [step_w, step_b]
            rest = find_force_line(held, stones - 1)
            if rest is not None:
                return [step_w, step_b] + rest
    return None


def render(cells: tuple[int, ...]) -> str:
    ch = {EMPTY: ".", WHITE: "W", BLACK: "B", ARROW: "X"}
    lines = []
    for rank in range(N - 1, -1, -1):
        lines.append("".join(ch[cells[rank * N + f]] for f in range(N)))
    return "\n".join(lines)
