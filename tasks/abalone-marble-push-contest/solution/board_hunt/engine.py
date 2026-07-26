"""Abalone marble-push rules (hex radius 2) — shared by oracle and tests."""
from __future__ import annotations

from functools import cache

DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
R = 2
EMPTY, BLACK, WHITE = 0, 1, 2
FLOOR = 1
BUDGET = 3


def _cells() -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for q in range(-R, R + 1):
        for r in range(-R, R + 1):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= R:
                out.append((q, r))
    return out


CELLS = _cells()
IDX = {c: i for i, c in enumerate(CELLS)}
N = len(CELLS)


def name(i: int) -> str:
    q, r = CELLS[i]
    return f"{chr(ord('a') + q + R)}{r + R + 1}"


def spot(s: str) -> int:
    if len(s) != 2 or s[0] < "a" or s[0] > "e" or s[1] < "1" or s[1] > "5":
        raise ValueError(f"bad cell {s}")
    q = ord(s[0]) - ord("a") - R
    r = int(s[1]) - R - 1
    if (q, r) not in IDX:
        raise ValueError(f"off-board cell {s}")
    return IDX[(q, r)]


def step(i: int, d: int) -> int | None:
    q, r = CELLS[i]
    dq, dr = DIRS[d]
    return IDX.get((q + dq, r + dr))


def parse_board(text: str) -> tuple[int, ...]:
    rows: list[str] = []
    started = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("board:"):
            started = True
            continue
        if not started:
            continue
        if not line.strip():
            if rows:
                break
            continue
        glyphs = "".join(ch for ch in line if ch in ".BW")
        if glyphs:
            rows.append(glyphs)
    expected_lens = [R + 1 + min(i, 2 * R - i) for i in range(2 * R + 1)]
    if [len(x) for x in rows] != expected_lens:
        raise ValueError(f"bad board shape {[len(x) for x in rows]} want {expected_lens}")
    board = [EMPTY] * N
    for vi, glyphs in enumerate(rows):
        r = R - vi
        qs = sorted(
            q for q in range(-R, R + 1) if max(abs(q), abs(r), abs(q + r)) <= R
        )
        if len(qs) != len(glyphs):
            raise ValueError("row/glyph mismatch")
        for q, ch in zip(qs, glyphs):
            board[IDX[(q, r)]] = {".": EMPTY, "B": BLACK, "W": WHITE}[ch]
    return tuple(board)


def _line_from(cells: tuple[int, ...], start: int, d: int, who: int) -> list[int]:
    out: list[int] = []
    cur: int | None = start
    while cur is not None and cells[cur] == who:
        out.append(cur)
        cur = step(cur, d)
    return out


def legal_moves(cells: tuple[int, ...], who: int) -> list[tuple]:
    foe = WHITE if who == BLACK else BLACK
    moves: list[tuple] = []
    seen: set[str] = set()
    own = [i for i, v in enumerate(cells) if v == who]

    for d in range(6):
        opp = (d + 3) % 6
        for i in own:
            group = _line_from(cells, i, d, who)
            for length in range(1, min(3, len(group)) + 1):
                rear = group[0]
                if rear != i:
                    break
                behind = step(rear, opp)
                if behind is not None and cells[behind] == who:
                    continue
                front = group[length - 1]
                land = step(front, d)
                if land is None:
                    continue
                if cells[land] == EMPTY:
                    mv = ("I", rear, length, d)
                    key = fmt_move(mv)
                    if key not in seen:
                        seen.add(key)
                        moves.append(mv)
                    continue
                if cells[land] != foe:
                    continue
                enemies = _line_from(cells, land, d, foe)
                n_en = len(enemies)
                if n_en == 0 or n_en >= length or n_en > 2:
                    continue
                beyond = step(enemies[-1], d)
                if beyond is not None and cells[beyond] != EMPTY:
                    continue
                mv = ("I", rear, length, d)
                key = fmt_move(mv)
                if key not in seen:
                    seen.add(key)
                    moves.append(mv)

    for axis in range(3):
        d_line = axis
        for i in own:
            group = _line_from(cells, i, d_line, who)
            if len(group) < 2:
                continue
            behind = step(group[0], (d_line + 3) % 6)
            if behind is not None and cells[behind] == who:
                continue
            for length in range(2, min(3, len(group)) + 1):
                members = group[:length]
                for side in range(6):
                    if side % 3 == axis:
                        continue
                    lands = [step(m, side) for m in members]
                    if any(L is None for L in lands):
                        continue
                    if any(cells[L] != EMPTY for L in lands):  # type: ignore[index]
                        continue
                    mv = ("S", tuple(members), side)
                    key = fmt_move(mv)
                    if key not in seen:
                        seen.add(key)
                        moves.append(mv)
    return moves


def fmt_move(mv: tuple) -> str:
    if mv[0] == "I":
        _, rear, length, d = mv
        cells_idx = []
        cur = rear
        for _ in range(length):
            cells_idx.append(cur)
            cur = step(cur, d)  # type: ignore[arg-type]
        front = cells_idx[-1]
        land = step(front, d)
        body = "".join(name(c) for c in cells_idx)
        if land is None:
            return f"{body}>off"
        return f"{body}>{name(land)}"
    _, ordered, side = mv
    body = "".join(name(c) for c in ordered)
    land = step(ordered[0], side)
    assert land is not None
    return f"{body}>{name(land)}"


def parse_move_on(cells: tuple[int, ...], s: str, who: int) -> tuple:
    s = s.strip()
    for mv in legal_moves(cells, who):
        if fmt_move(mv) == s:
            return mv
    raise ValueError(f"illegal or unknown move {s}")


def apply_move(
    cells: tuple[int, ...], mv: tuple, who: int
) -> tuple[tuple[int, ...], int]:
    foe = WHITE if who == BLACK else BLACK
    board = list(cells)
    ejected = 0
    if mv[0] == "I":
        _, rear, length, d = mv
        chain = []
        cur = rear
        for _ in range(length):
            chain.append(cur)
            cur = step(cur, d)  # type: ignore[arg-type]
        front = chain[-1]
        land = step(front, d)
        if land is None:
            raise ValueError("suicide inline")
        if cells[land] == EMPTY:
            for c in chain:
                board[c] = EMPTY
            for c in chain:
                nxt = step(c, d)
                assert nxt is not None
                board[nxt] = who
            return tuple(board), 0
        enemies = []
        cur = land
        while cur is not None and cells[cur] == foe:
            enemies.append(cur)
            cur = step(cur, d)
        for e in reversed(enemies):
            board[e] = EMPTY
        for e in reversed(enemies):
            dest = step(e, d)
            if dest is None:
                if foe == WHITE:
                    ejected += 1
            else:
                board[dest] = foe
        for c in chain:
            board[c] = EMPTY
        for c in chain:
            nxt = step(c, d)
            assert nxt is not None
            board[nxt] = who
        return tuple(board), ejected

    _, ordered, side = mv
    lands = []
    for c in ordered:
        L = step(c, side)
        assert L is not None and cells[L] == EMPTY
        lands.append(L)
    for c in ordered:
        board[c] = EMPTY
    for L in lands:
        board[L] = who
    return tuple(board), 0


def goal_met(ejected_so_far: int) -> bool:
    return ejected_so_far >= FLOOR


@cache
def can_force(cells: tuple[int, ...], stones: int, ejected: int) -> bool:
    if goal_met(ejected):
        return True
    if stones <= 0:
        return False
    moves = legal_moves(cells, BLACK)
    if not moves:
        return False
    for mv in moves:
        after, ej = apply_move(cells, mv, BLACK)
        ne = ejected + ej
        if goal_met(ne):
            return True
        if stones == 1:
            continue
        replies = legal_moves(after, WHITE)
        if not replies:
            if can_force(after, stones - 1, ne):
                return True
            continue
        if all(
            can_force(apply_move(after, r, WHITE)[0], stones - 1, ne) for r in replies
        ):
            return True
    return False


@cache
def can_coop(cells: tuple[int, ...], stones: int, ejected: int) -> bool:
    if goal_met(ejected):
        return True
    if stones <= 0:
        return False
    for mv in legal_moves(cells, BLACK):
        after, ej = apply_move(cells, mv, BLACK)
        ne = ejected + ej
        if goal_met(ne) or can_coop(after, stones - 1, ne):
            return True
    return False


def verdict(cells: tuple[int, ...]) -> str:
    can_force.cache_clear()
    can_coop.cache_clear()
    if can_force(cells, BUDGET, 0):
        return "win"
    if can_coop(cells, BUDGET, 0):
        return "trap"
    return "fort"


def threats(cells: tuple[int, ...]) -> list[tuple]:
    out = []
    for mv in legal_moves(cells, BLACK):
        after, ej = apply_move(cells, mv, BLACK)
        if goal_met(ej):
            continue
        for mv2 in legal_moves(after, BLACK):
            _, ej2 = apply_move(after, mv2, BLACK)
            if goal_met(ej + ej2):
                out.append(mv)
                break
    return out


def forcing_first_moves(cells: tuple[int, ...]) -> set[str]:
    out = set()
    for mv in legal_moves(cells, BLACK):
        after, ej = apply_move(cells, mv, BLACK)
        if goal_met(ej):
            out.add(fmt_move(mv))
            continue
        replies = legal_moves(after, WHITE)
        if not replies:
            if can_force(after, BUDGET - 1, ej):
                out.add(fmt_move(mv))
        elif all(
            can_force(apply_move(after, r, WHITE)[0], BUDGET - 1, ej) for r in replies
        ):
            out.add(fmt_move(mv))
    return out


def find_coop_line(cells: tuple[int, ...], stones: int = BUDGET) -> list[str] | None:
    def dfs(cur, left, ej, path):
        if goal_met(ej):
            return path
        if left <= 0:
            return None
        for mv in legal_moves(cur, BLACK):
            after, e = apply_move(cur, mv, BLACK)
            got = dfs(after, left - 1, ej + e, path + [f"black {fmt_move(mv)}"])
            if got is not None:
                return got
        return None

    return dfs(cells, stones, 0, [])


def find_force_line(cells: tuple[int, ...]) -> list[str] | None:
    def force(cur, left, ej, path):
        if goal_met(ej):
            return path
        if left <= 0:
            return None
        for mv in legal_moves(cur, BLACK):
            after, e = apply_move(cur, mv, BLACK)
            ne = ej + e
            step_path = path + [f"black {fmt_move(mv)}"]
            if goal_met(ne):
                return step_path
            replies = legal_moves(after, WHITE)
            if not replies:
                got = force(after, left - 1, ne, step_path)
                if got is not None:
                    return got
                continue
            if all(
                can_force(apply_move(after, r, WHITE)[0], left - 1, ne) for r in replies
            ):
                r0 = replies[0]
                after_w, _ = apply_move(after, r0, WHITE)
                got = force(
                    after_w, left - 1, ne, step_path + [f"white {fmt_move(r0)}"]
                )
                if got is not None:
                    return got
        return None

    can_force.cache_clear()
    return force(cells, BUDGET, 0, [])


def find_refutation(cells: tuple[int, ...], threat: tuple) -> str | None:
    after, ej = apply_move(cells, threat, BLACK)
    if goal_met(ej):
        return None
    for r in legal_moves(after, WHITE):
        held, _ = apply_move(after, r, WHITE)
        if not any(
            goal_met(ej + apply_move(held, m2, BLACK)[1])
            for m2 in legal_moves(held, BLACK)
        ):
            return fmt_move(r)
    return None


def sheet_text(board_id: str, cells: tuple[int, ...]) -> str:
    lines = [f"board_id: {board_id}", "to_move: black", "board:"]
    for vi in range(2 * R + 1):
        r = R - vi
        qs = sorted(
            q for q in range(-R, R + 1) if max(abs(q), abs(r), abs(q + r)) <= R
        )
        pad = " " * (5 - len(qs))
        glyphs = "".join(".BW"[cells[IDX[(q, r)]]] for q in qs)
        lines.append(pad + glyphs)
    return "\n".join(lines) + "\n"
