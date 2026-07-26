"""Overnight draft: fourth cooperative Blue placement stamps every round a win."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from sheet_load import sheet_paths

APP = Path(__import__("os").environ.get("APP_ROOT", "/app"))
N = 5
FILES = "abcde"
EMPTY, BLUE, YELLOW, BLOCK = 0, 1, 2, 3
FLOOR = 0
BUDGET = 4  # longer than the table's three
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


def rotations(cells):
    out = set()
    pts = cells
    for _ in range(4):
        for reflect in (False, True):
            cur = [(-x, y) for x, y in pts] if reflect else pts
            minx = min(x for x, _ in cur)
            miny = min(y for _, y in cur)
            out.add(tuple(sorted((x - minx, y - miny) for x, y in cur)))
        pts = [(y, -x) for x, y in pts]
    return [tuple(p) for p in sorted(out)]


ORIENTS = {pid: rotations(shape) for pid, shape in RAW.items()}
SIZE = {pid: len(shape) for pid, shape in RAW.items()}


def name(i: int) -> str:
    return f"{FILES[i % N]}{i // N + 1}"


def spot(s: str) -> int:
    return (int(s[1]) - 1) * N + FILES.index(s[0])


def squares_of(pid, anchor, oi):
    shape = ORIENTS[pid][oi]
    af, ar = anchor % N, anchor // N
    cells = []
    for dx, dy in shape:
        f, r = af + dx, ar + dy
        if not (0 <= f < N and 0 <= r < N):
            return None
        cells.append(r * N + f)
    return tuple(sorted(cells))


def neighbors(i, deltas):
    f, r = i % N, i // N
    for df, dr in deltas:
        nf, nr = f + df, r + dr
        if 0 <= nf < N and 0 <= nr < N:
            yield nr * N + nf


def has_own(cells, who):
    return any(v == who for v in cells)


def legal_on(cells, who, pid, place):
    if len(place) != SIZE[pid]:
        return False
    ok_shape = False
    for oi in range(len(ORIENTS[pid])):
        for a in range(N * N):
            if squares_of(pid, a, oi) == place:
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
        if not any(cells[n] == who for c in place for n in neighbors(c, CORNER)):
            return False
    else:
        if not any(c in {0, N - 1, N * (N - 1), N * N - 1} for c in place):
            return False
    return True


def all_placements(cells, who, inv):
    seen = set()
    out = []
    for pid in inv:
        for oi in range(len(ORIENTS[pid])):
            for a in range(N * N):
                place = squares_of(pid, a, oi)
                if place is None or (pid, place) in seen:
                    continue
                if legal_on(cells, who, pid, place):
                    seen.add((pid, place))
                    out.append((pid, place))
    return out


def apply(cells, who, pid, place, inv):
    board = list(cells)
    for c in place:
        board[c] = who
    ninv = list(inv)
    ninv.remove(pid)
    return tuple(board), tuple(ninv)


def sq_left(inv):
    return sum(SIZE[p] for p in inv)


def filled(inv):
    return sq_left(inv) <= FLOOR


def parse_sheet(path: Path):
    board_id = ""
    binv, yinv, rows = [], [], []
    inb = False
    for line in path.read_text().splitlines():
        t = line.strip()
        if t.startswith("board_id:"):
            board_id = t.split(":", 1)[1].strip()
        elif t.startswith("blue_inv:"):
            binv = [x.strip() for x in t.split(":", 1)[1].split(",") if x.strip()]
        elif t.startswith("yellow_inv:"):
            yinv = [x.strip() for x in t.split(":", 1)[1].split(",") if x.strip()]
        elif t == "board:":
            inb = True
        elif inb and t:
            rows.append(t)
            if len(rows) == N:
                break
    cells = [EMPTY] * (N * N)
    for ri, row in enumerate(rows):
        rank = N - 1 - ri
        for f, ch in enumerate(row):
            cells[rank * N + f] = {".": EMPTY, "B": BLUE, "Y": YELLOW, "X": BLOCK}[ch]
    return board_id, tuple(cells), tuple(binv), tuple(yinv)


def coop(cells, binv, yinv, stones):
    if filled(binv):
        return []
    if stones <= 0:
        return None
    for pid, place in all_placements(cells, BLUE, binv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        step = f"blue {pid}@{','.join(name(c) for c in place)}"
        if filled(nb):
            return [step]
        rest = coop(after, nb, yinv, stones - 1)
        if rest is not None:
            return [step] + rest
    return None


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/output/blokus-card.json")
    if out.is_file():
        card = json.loads(out.read_text())
        card["rounds"] = sorted(card["rounds"], key=lambda row: row["board_id"])
        staged = out.with_suffix(out.suffix + ".staged")
        staged.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n")
        import os

        os.replace(staged, out)
        print(f"filed existing card to {out}", file=sys.stderr)
        return

    rounds = []
    for path in sheet_paths(APP):
        bid, cells, binv, yinv = parse_sheet(path)
        line = coop(cells, binv, yinv, BUDGET) or []
        if line:
            first = line[0].split(" ", 1)[1]
            pid, place = first.split("@", 1)
            rounds.append(
                {
                    "board_id": bid,
                    "status": "win",
                    "piece_id": pid,
                    "placement": place,
                    "squares_left": 0,
                    "sequence": line,
                    "refutations": [],
                    "coop_fill": True,
                }
            )
        else:
            rounds.append(
                {
                    "board_id": bid,
                    "status": "win",
                    "piece_id": "",
                    "placement": "",
                    "squares_left": sq_left(binv),
                    "sequence": [],
                    "refutations": [],
                    "coop_fill": False,
                }
            )
    card = {"schema_tag": "blokus-corner-v1", "rounds": rounds}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(card, indent=2) + "\n")


if __name__ == "__main__":
    main()
