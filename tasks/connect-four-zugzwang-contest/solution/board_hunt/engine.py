"""Connect Four engine for booklet generation and oracle classification.

Standard 6x7 gravity board. Yellow (1) to move. Columns 0..6, rows 0..5 bottom-up.
House budget: Yellow drops <= BUDGET for win/trap lines.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import cache

ROWS, COLS = 6, 7
EMPTY, YELLOW, RED = 0, 1, 2
BUDGET = 5  # Yellow drops
PAD_BAIT = 7  # kiosk inflated cooperative hunt

Board = tuple[int, ...]  # length 42, index = row * COLS + col


def idx(r: int, c: int) -> int:
    return r * COLS + c


def height(board: Board, c: int) -> int:
    h = 0
    while h < ROWS and board[idx(h, c)] != EMPTY:
        h += 1
    return h


def legal_cols(board: Board) -> list[int]:
    return [c for c in range(COLS) if height(board, c) < ROWS]


def drop(board: Board, c: int, who: int) -> Board:
    h = height(board, c)
    if h >= ROWS:
        raise ValueError(f"column {c} full")
    cells = list(board)
    cells[idx(h, c)] = who
    return tuple(cells)


def winner(board: Board) -> int:
    """Return YELLOW/RED if that side has four, else EMPTY."""
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


def threat_cells(board: Board, who: int) -> list[tuple[int, int]]:
    """Empty cells that complete a four for `who` if filled (ignoring gravity)."""
    out: list[tuple[int, int]] = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[idx(r, c)] != EMPTY:
                continue
            cells = list(board)
            cells[idx(r, c)] = who
            if winner(tuple(cells)) == who:
                out.append((c, r))
    return out


def gravity_threats(board: Board, who: int) -> list[tuple[int, int]]:
    """Threat cells that are currently the gravity landing of their column."""
    out = []
    for c, r in threat_cells(board, who):
        if height(board, c) == r:
            out.append((c, r))
    return out


def odd_even_note(c: int, r: int) -> str:
    # House rows are 1..6 from bottom; odd favors Yellow-to-move.
    house_row = r + 1
    side = "yellow-odd" if house_row % 2 == 1 else "red-even"
    return f"col{c}-row{house_row}-{side}"


@cache
def can_force(board: Board, stones: int) -> bool:
    if winner(board) == YELLOW:
        return True
    if winner(board) == RED:
        return False
    if stones <= 0:
        return False
    cols = legal_cols(board)
    if not cols:
        return False
    for c in cols:
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            return True
        if stones == 1:
            continue
        rcols = legal_cols(after)
        if not rcols:
            if can_force(after, stones - 1):
                return True
            continue
        # Red fights: Yellow must win against every Red reply.
        if all(can_force(drop(after, rc, RED), stones - 1) for rc in rcols):
            return True
    return False


@cache
def can_coop(board: Board, stones: int) -> bool:
    if winner(board) == YELLOW:
        return True
    if winner(board) == RED:
        return False
    if stones <= 0:
        return False
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            return True
        if can_coop(after, stones - 1):
            return True
    return False


def find_force_line(board: Board, stones: int) -> list[tuple[str, int]] | None:
    """Return sequence of (side, col) ending in Yellow connect-4, or None."""
    if winner(board) == YELLOW:
        return []
    if winner(board) == RED or stones <= 0:
        return None
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            return [("yellow", c)]
        if stones == 1:
            continue
        rcols = legal_cols(after)
        if not rcols:
            rest = find_force_line(after, stones - 1)
            if rest is not None:
                return [("yellow", c)] + rest
            continue
        # Prefer a line that works vs all replies; pick any reply branch for the witness.
        if all(can_force(drop(after, rc, RED), stones - 1) for rc in rcols):
            # Witness: pick the reply that still forces with a concrete PV.
            for rc in rcols:
                mid = drop(after, rc, RED)
                rest = find_force_line(mid, stones - 1)
                if rest is not None:
                    return [("yellow", c), ("red", rc)] + rest
    return None


def find_coop_line(board: Board, stones: int) -> list[int] | None:
    if winner(board) == YELLOW:
        return []
    if winner(board) == RED or stones <= 0:
        return None
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            return [c]
        rest = find_coop_line(after, stones - 1)
        if rest is not None:
            return [c] + rest
    return None


def immediate_threats(board: Board) -> list[int]:
    """Yellow first columns that do not win now, but win on next Yellow if Red passes."""
    threats = []
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            continue
        if can_coop(after, 1):
            threats.append(c)
    return threats


def refute_threat(board: Board, threat_col: int) -> int | None:
    after = drop(board, threat_col, YELLOW)
    if winner(after) == YELLOW:
        return None
    for rc in legal_cols(after):
        mid = drop(after, rc, RED)
        if not can_coop(mid, 1):
            return rc
    return None


def losing_first_drops(board: Board) -> list[tuple[int, int]]:
    """Yellow first columns that let Red win on the next Red drop; reply is that winning col."""
    out = []
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            continue
        for rc in legal_cols(after):
            mid = drop(after, rc, RED)
            if winner(mid) == RED:
                out.append((c, rc))
                break
    return out


def classify(board: Board) -> dict:
    force = can_force(board, BUDGET)
    coop = can_coop(board, BUDGET)
    if force:
        status = "win"
    elif coop:
        status = "trap"
    else:
        status = "draw"

    threats = [{"column": c, "row": height(board, c)} for c in immediate_threats(board)]
    # Attach actual landing row after drop for threat cells that matter for parity docs.
    refined = []
    for t in threats:
        c = t["column"]
        after_h = height(board, c)  # landing row
        refined.append({"column": c, "row": after_h})
    threats = refined

    refutations: list[dict] = []
    if status == "trap":
        for t in threats:
            reply = refute_threat(board, t["column"])
            if reply is not None:
                refutations.append({"column": t["column"], "reply": reply})
    elif status == "draw":
        for col, reply in losing_first_drops(board):
            refutations.append({"column": col, "reply": reply})
        # Also cover trap-style threats if any exist under inflated bait.
        for t in threats:
            reply = refute_threat(board, t["column"])
            if reply is not None and not any(r["column"] == t["column"] for r in refutations):
                refutations.append({"column": t["column"], "reply": reply})

    sequence: list[str] = []
    best_column = -1
    win_in = 0
    if status == "win":
        line = find_force_line(board, BUDGET)
        assert line is not None
        sequence = [f"{side} {col}" for side, col in line]
        best_column = line[0][1]
        win_in = sum(1 for side, _ in line if side == "yellow")
    elif status == "trap":
        line = find_coop_line(board, BUDGET)
        assert line is not None
        sequence = [f"yellow {c}" for c in line]
        best_column = line[0]
        win_in = len(line)

    gthreats = gravity_threats(board, YELLOW)
    return {
        "status": status,
        "best_column": best_column,
        "win_in": win_in,
        "sequence": sequence,
        "threats": threats if status in ("trap", "draw") else [],
        "refutations": refutations if status in ("trap", "draw") else [],
        "coop_win": coop,
        "force": force,
        "gravity_threats": gthreats,
        "notes": [odd_even_note(c, r) for c, r in gthreats],
    }


def parse_grid(rows: Iterable[str]) -> Board:
    """rows: 6 strings of length 7, top rank first (as printed)."""
    lines = list(rows)
    assert len(lines) == ROWS
    cells = [EMPTY] * (ROWS * COLS)
    for ri, line in enumerate(lines):
        assert len(line) == COLS, line
        rank = ROWS - 1 - ri
        for c, ch in enumerate(line):
            cells[idx(rank, c)] = {".": EMPTY, "Y": YELLOW, "R": RED, "y": YELLOW, "r": RED}[ch]
    return tuple(cells)


def render(board: Board) -> str:
    lines = []
    for rank in range(ROWS - 1, -1, -1):
        lines.append("".join(".YR"[board[idx(rank, c)]] for c in range(COLS)))
    return "\n".join(lines)


def clear_caches() -> None:
    can_force.cache_clear()
    can_coop.cache_clear()
