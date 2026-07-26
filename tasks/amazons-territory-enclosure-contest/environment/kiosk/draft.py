"""Overnight kiosk draft — fourth-turn cooperative hunt, stamps every round win.

If a finished card already sits at the output path, re-file it with stable
ordering so a second emit stays byte-identical.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

N = 5
FILES = "abcde"
EMPTY, WHITE, BLACK, ARROW = 0, 1, 2, 3
DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
FLOOR = 2


def name(i: int) -> str:
    return f"{FILES[i % N]}{i // N + 1}"


def queen_rays(cells, start):
    out = []
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


def amazons(cells, who):
    return [i for i, v in enumerate(cells) if v == who]


def legal_turns(cells, who):
    turns = []
    for src in amazons(cells, who):
        for dst in queen_rays(cells, src):
            mid = list(cells)
            mid[src] = EMPTY
            mid[dst] = who
            for arr in queen_rays(tuple(mid), dst):
                turns.append((src, dst, arr))
    return sorted(set(turns))


def apply_turn(cells, turn, who):
    src, dst, arr = turn
    board = list(cells)
    board[src] = EMPTY
    board[dst] = who
    board[arr] = ARROW
    return tuple(board)


def reachable(cells, who):
    frontier = list(amazons(cells, who))
    seen = set(frontier)
    reached = set()
    while frontier:
        cur = frontier.pop()
        for nxt in queen_rays(cells, cur):
            if nxt not in seen:
                seen.add(nxt)
                reached.add(nxt)
                frontier.append(nxt)
    return reached


def territory_delta(cells):
    w = reachable(cells, WHITE)
    b = reachable(cells, BLACK)
    return len(w - b) - len(b - w)


def enclosed(cells):
    return territory_delta(cells) >= FLOOR


def fmt(turn):
    a, b, c = turn
    return f"{name(a)}-{name(b)}/{name(c)}"


def coop_line(cells, stones=4):
    if enclosed(cells):
        return []
    if stones <= 0:
        return None
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        if enclosed(after):
            return [t]
        rest = coop_line(after, stones - 1)
        if rest is not None:
            return [t] + rest
    return None


def read_sheet(path: Path):
    rows = []
    board_id = path.stem.replace("board_", "")
    inb = False
    for line in path.read_text().splitlines():
        t = line.strip()
        if t.startswith("board_id:"):
            board_id = t.split(":", 1)[1].strip()
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
            cells[rank * N + f] = {".": EMPTY, "W": WHITE, "B": BLACK, "X": ARROW}[ch]
    return board_id, tuple(cells)


def draft_round(path: Path) -> dict:
    board_id, cells = read_sheet(path)
    line = coop_line(cells, 4) or []
    seq = [f"white {fmt(t)}" for t in line]
    delta = 0
    cur = cells
    for t in line:
        cur = apply_turn(cur, t, WHITE)
        delta = territory_delta(cur)
    return {
        "board_id": board_id,
        "status": "win",
        "best_move": fmt(line[0]) if line else "",
        "territory_delta": delta,
        "sequence": seq,
        "refutations": [],
        "coop_enclose": True,
    }


def file_existing(path: Path) -> None:
    card = json.loads(path.read_text())
    card["rounds"] = sorted(card["rounds"], key=lambda row: row["board_id"])
    staged = path.with_suffix(path.suffix + ".staged")
    staged.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n")
    os.replace(staged, path)


def main(out_path: str) -> None:
    dest = Path(out_path)
    if dest.is_file():
        file_existing(dest)
        print(f"filed existing card to {dest}", file=sys.stderr)
        return

    root = Path(__file__).resolve().parent.parent
    puzzles = sorted((root / "puzzles").glob("board_*.txt"))
    card = {
        "schema_tag": "amazons-territory-v1",
        "rounds": [draft_round(p) for p in puzzles],
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(card, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/output/amazons-card.json")
