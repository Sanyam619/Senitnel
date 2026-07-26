"""Blokus corner-contact engine + booklet curator (authoring only)."""
from __future__ import annotations

from functools import cache

N = 5
FILES = "abcde"
EMPTY, BLUE, YELLOW, BLOCK = 0, 1, 2, 3
FLOOR = 0  # blue must empty inventory (squares_left <= 0)
BUDGET = 3
EDGE = ((-1, 0), (1, 0), (0, -1), (0, 1))
CORNER = ((-1, -1), (-1, 1), (1, -1), (1, 1))

RAW = {
    "1": [(0, 0)],
    "2": [(0, 0), (1, 0)],
    "I3": [(0, 0), (1, 0), (2, 0)],
    "V3": [(0, 0), (0, 1), (1, 0)],
    "I4": [(0, 0), (1, 0), (2, 0), (3, 0)],
    "O4": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T4": [(0, 0), (1, 0), (2, 0), (1, 1)],
    "L4": [(0, 0), (0, 1), (0, 2), (1, 2)],
    "S4": [(1, 0), (2, 0), (0, 1), (1, 1)],
}


def name(i: int) -> str:
    return f"{FILES[i % N]}{i // N + 1}"


def spot(s: str) -> int:
    return (int(s[1]) - 1) * N + FILES.index(s[0])


def rotations(cells: list[tuple[int, int]]) -> list[tuple[tuple[int, int], ...]]:
    out: set[tuple[tuple[int, int], ...]] = set()
    pts = cells
    for _ in range(4):
        for reflect in (False, True):
            cur = pts
            if reflect:
                cur = [(-x, y) for x, y in cur]
            minx = min(x for x, _ in cur)
            miny = min(y for _, y in cur)
            norm = tuple(sorted((x - minx, y - miny) for x, y in cur))
            out.add(norm)
        pts = [(y, -x) for x, y in pts]
    return [tuple(p) for p in sorted(out)]


ORIENTS = {pid: rotations(shape) for pid, shape in RAW.items()}
SIZE = {pid: len(shape) for pid, shape in RAW.items()}


def neighbors(i: int, deltas):
    f, r = i % N, i // N
    for df, dr in deltas:
        nf, nr = f + df, r + dr
        if 0 <= nf < N and 0 <= nr < N:
            yield nr * N + nf


def squares_of(pid: str, anchor: int, oi: int) -> tuple[int, ...] | None:
    shape = ORIENTS[pid][oi]
    af, ar = anchor % N, anchor // N
    cells = []
    for dx, dy in shape:
        f, r = af + dx, ar + dy
        if not (0 <= f < N and 0 <= r < N):
            return None
        cells.append(r * N + f)
    return tuple(sorted(cells))


def fmt_placement(pid: str, cells: tuple[int, ...]) -> str:
    return f"{pid}@{','.join(name(c) for c in cells)}"


def parse_placement(s: str) -> tuple[str, tuple[int, ...]]:
    pid, rest = s.split("@", 1)
    cells = tuple(sorted(spot(x) for x in rest.split(",")))
    return pid, cells


def has_own(cells: tuple[int, ...], who: int) -> bool:
    return any(v == who for v in cells)


def legal_on(
    cells: tuple[int, ...], who: int, pid: str, place: tuple[int, ...]
) -> bool:
    if len(place) != SIZE[pid]:
        return False
    ok_shape = False
    for oi in range(len(ORIENTS[pid])):
        for a in range(N * N):
            got = squares_of(pid, a, oi)
            if got == place:
                ok_shape = True
                break
        if ok_shape:
            break
    if not ok_shape:
        return False
    for c in place:
        if cells[c] != EMPTY:
            return False
    for c in place:
        for n in neighbors(c, EDGE):
            if n not in place and cells[n] == who:
                return False
    if has_own(cells, who):
        corner_ok = False
        for c in place:
            for n in neighbors(c, CORNER):
                if cells[n] == who:
                    corner_ok = True
                    break
            if corner_ok:
                break
        if not corner_ok:
            return False
    else:
        corners = {0, N - 1, N * (N - 1), N * N - 1}
        if not any(c in corners for c in place):
            return False
    return True


def all_placements(
    cells: tuple[int, ...], who: int, inv: tuple[str, ...]
) -> list[tuple[str, tuple[int, ...]]]:
    out: list[tuple[str, tuple[int, ...]]] = []
    seen: set[tuple[str, tuple[int, ...]]] = set()
    for pid in inv:
        for oi in range(len(ORIENTS[pid])):
            for a in range(N * N):
                place = squares_of(pid, a, oi)
                if place is None:
                    continue
                key = (pid, place)
                if key in seen:
                    continue
                if legal_on(cells, who, pid, place):
                    seen.add(key)
                    out.append(key)
    return out


def apply(
    cells: tuple[int, ...],
    who: int,
    pid: str,
    place: tuple[int, ...],
    inv: tuple[str, ...],
) -> tuple[tuple[int, ...], tuple[str, ...]]:
    if pid not in inv:
        raise ValueError("piece not in inventory")
    if not legal_on(cells, who, pid, place):
        raise ValueError("illegal")
    board = list(cells)
    for c in place:
        board[c] = who
    ninv = list(inv)
    ninv.remove(pid)
    return tuple(board), tuple(ninv)


def sq_left(inv: tuple[str, ...]) -> int:
    return sum(SIZE[p] for p in inv)


def filled(inv: tuple[str, ...]) -> bool:
    return sq_left(inv) <= FLOOR


@cache
def can_force(
    cells: tuple[int, ...],
    binv: tuple[str, ...],
    yinv: tuple[str, ...],
    stones: int,
) -> bool:
    if filled(binv):
        return True
    if stones <= 0:
        return False
    moves = all_placements(cells, BLUE, binv)
    if not moves:
        return filled(binv)
    for pid, place in moves:
        after, nb = apply(cells, BLUE, pid, place, binv)
        if filled(nb):
            return True
        if stones == 1:
            continue
        ymoves = all_placements(after, YELLOW, yinv)
        if not ymoves:
            if can_force(after, nb, yinv, stones - 1):
                return True
            continue
        ok = True
        for yp, ypl in ymoves:
            ya, ny = apply(after, YELLOW, yp, ypl, yinv)
            if not can_force(ya, nb, ny, stones - 1):
                ok = False
                break
        if ok:
            return True
    return False


@cache
def can_coop(
    cells: tuple[int, ...],
    binv: tuple[str, ...],
    yinv: tuple[str, ...],
    stones: int,
) -> bool:
    if filled(binv):
        return True
    if stones <= 0:
        return False
    for pid, place in all_placements(cells, BLUE, binv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        if filled(nb) or can_coop(after, nb, yinv, stones - 1):
            return True
    return False


def verdict(cells, binv, yinv) -> str:
    can_force.cache_clear()
    can_coop.cache_clear()
    if can_force(cells, binv, yinv, BUDGET):
        return "win"
    if can_coop(cells, binv, yinv, BUDGET):
        return "trap"
    return "fort"


def threats(cells, binv, yinv):
    out = []
    for pid, place in all_placements(cells, BLUE, binv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        if filled(nb):
            continue
        for pid2, place2 in all_placements(after, BLUE, nb):
            __after2, nb2 = apply(after, BLUE, pid2, place2, nb)
            if filled(nb2):
                out.append((pid, place))
                break
    return out


def parse_board_text(text: str):
    board_id = ""
    binv: list[str] = []
    yinv: list[str] = []
    rows: list[str] = []
    inb = False
    for line in text.splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if t.startswith("board_id:"):
            board_id = t.split(":", 1)[1].strip()
        elif t.startswith("blue_inv:"):
            raw = t.split(":", 1)[1].strip()
            binv = [x.strip() for x in raw.split(",") if x.strip()]
        elif t.startswith("yellow_inv:"):
            raw = t.split(":", 1)[1].strip()
            yinv = [x.strip() for x in raw.split(",") if x.strip()]
        elif t == "board:":
            inb = True
        elif inb:
            rows.append(t)
            if len(rows) == N:
                break
    cells = [EMPTY] * (N * N)
    for ri, row in enumerate(rows):
        rank = N - 1 - ri
        for f, ch in enumerate(row):
            cells[rank * N + f] = {".": EMPTY, "B": BLUE, "Y": YELLOW, "X": BLOCK}[ch]
    return board_id, tuple(cells), tuple(binv), tuple(yinv)
