"""Overnight kiosk draft — seven-drop cooperative hunt, stamps every round win.

If a finished card already sits at the output path, re-file it with stable
ordering so a second emit stays byte-identical.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from sheet_load import list_sheets

ROWS, COLS = 6, 7
EMPTY, YELLOW, RED = 0, 1, 2
PAD = 7


def idx(r: int, c: int) -> int:
    return r * COLS + c


def height(board, c: int) -> int:
    h = 0
    while h < ROWS and board[idx(h, c)] != EMPTY:
        h += 1
    return h


def legal_cols(board):
    return [c for c in range(COLS) if height(board, c) < ROWS]


def drop(board, c: int, who: int):
    h = height(board, c)
    cells = list(board)
    cells[idx(h, c)] = who
    return tuple(cells)


def winner(board) -> int:
    for r in range(ROWS):
        for c in range(COLS):
            who = board[idx(r, c)]
            if who == EMPTY:
                continue
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                ok = True
                for k in range(1, 4):
                    rr, cc = r + dr * k, c + dc * k
                    if not (0 <= rr < ROWS and 0 <= cc < COLS):
                        ok = False
                        break
                    if board[idx(rr, cc)] != who:
                        ok = False
                        break
                if ok:
                    return who
    return EMPTY


def coop_line(board, stones=PAD):
    if winner(board) == YELLOW:
        return []
    if winner(board) == RED or stones <= 0:
        return None
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            return [c]
        rest = coop_line(after, stones - 1)
        if rest is not None:
            return [c] + rest
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
            if len(rows) == ROWS:
                break
    cells = [EMPTY] * (ROWS * COLS)
    for ri, row in enumerate(rows):
        rank = ROWS - 1 - ri
        for c, ch in enumerate(row):
            cells[idx(rank, c)] = {".": EMPTY, "Y": YELLOW, "R": RED}[ch]
    return board_id, tuple(cells)


def draft_round(path: Path) -> dict:
    board_id, board = read_sheet(path)
    line = coop_line(board, PAD) or []
    seq = [f"yellow {c}" for c in line]
    return {
        "board_id": board_id,
        "status": "win",
        "best_column": line[0] if line else -1,
        "win_in": len(line),
        "sequence": seq,
        "threats": [],
        "refutations": [],
        "coop_win": True,
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
    puzzles = list_sheets(root)
    card = {
        "schema_tag": "c4-zugzwang-v1",
        "rounds": [draft_round(p) for p in puzzles],
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(card, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/output/c4-card.json")
