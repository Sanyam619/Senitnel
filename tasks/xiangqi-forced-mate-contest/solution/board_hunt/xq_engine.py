"""Xiangqi rules + mate search for booklet design / oracle / verifier."""
from __future__ import annotations

from copy import deepcopy

FILES = "abcdefghi"
# ranks 0..9; Red palace ranks 0-2, Black 7-9; river between 4 and 5
RED_PAL = {(f, r) for f in range(3, 6) for r in range(0, 3)}
BLK_PAL = {(f, r) for f in range(3, 6) for r in range(7, 10)}


def parse_sq(s: str) -> tuple[int, int]:
    return ord(s[0]) - 97, int(s[1])


def sq_name(f: int, r: int) -> str:
    return f"{FILES[f]}{r}"


def load_sheet(path: str) -> tuple[list[list[str | None]], str]:
    text = open(path).read()
    to_move = "r"
    rows: list[str] = []
    in_board = False
    for line in text.splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if t.startswith("to_move:"):
            to_move = "r" if "red" in t.lower() else "b"
        elif t == "board:":
            in_board = True
        elif in_board:
            rows.append(t)
            if len(rows) == 10:
                in_board = False
    if len(rows) != 10:
        raise ValueError(f"need 10 ranks in {path}")
    # rows[0] is rank 9 (top); rows[9] is rank 0
    board: list[list[str | None]] = [[None] * 9 for _ in range(10)]
    for i, row in enumerate(rows):
        if len(row) != 9:
            raise ValueError(f"bad row {row!r} in {path}")
        rank = 9 - i
        for f, ch in enumerate(row):
            if ch == ".":
                continue
            color = "r" if ch.isupper() else "b"
            board[rank][f] = color + ch.lower()
    return board, to_move


def dump_board(board: list[list[str | None]]) -> str:
    lines = []
    for rank in range(9, -1, -1):
        s = ""
        for f in range(9):
            p = board[rank][f]
            if p is None:
                s += "."
            else:
                ch = p[1].upper() if p[0] == "r" else p[1]
                s += ch
        lines.append(s)
    return "\n".join(lines)


def board_key(board: list[list[str | None]]) -> tuple:
    return tuple(tuple(row) for row in board)


def find_king(board, color: str) -> tuple[int, int] | None:
    for r in range(10):
        for f in range(9):
            p = board[r][f]
            if p and p[0] == color and p[1] == "k":
                return f, r
    return None


def facing_ok(board) -> bool:
    rk = find_king(board, "r")
    bk = find_king(board, "b")
    if rk is None or bk is None:
        return True
    rf, rr = rk
    bf, br = bk
    if rf != bf:
        return True
    lo, hi = sorted((rr, br))
    for r in range(lo + 1, hi):
        if board[r][rf] is not None:
            return True
    return False


def in_bounds(f, r) -> bool:
    return 0 <= f < 9 and 0 <= r < 10


def attacked_by(board, f, r, by: str) -> bool:
    """True if square (f,r) is attacked by side `by`."""
    for sr in range(10):
        for sf in range(9):
            p = board[sr][sf]
            if not p or p[0] != by:
                continue
            kind = p[1]
            if kind == "k":
                if abs(sf - f) + abs(sr - r) == 1 and abs(sf - f) <= 1 and abs(sr - r) <= 1:
                    if (sf, sr) in (RED_PAL if by == "r" else BLK_PAL) and (f, r) in (
                        RED_PAL if by == "r" else BLK_PAL
                    ):
                        if (abs(sf - f) == 1 and sr == r) or (abs(sr - r) == 1 and sf == f):
                            return True
                # flying general
                if sf == f:
                    lo, hi = sorted((sr, r))
                    blocked = any(board[rr][sf] is not None for rr in range(lo + 1, hi))
                    if not blocked:
                        opp = find_king(board, "b" if by == "r" else "r")
                        if opp == (f, r):
                            return True
            elif kind == "a":
                if abs(sf - f) == 1 and abs(sr - r) == 1:
                    pal = RED_PAL if by == "r" else BLK_PAL
                    if (sf, sr) in pal and (f, r) in pal:
                        return True
            elif kind == "b":  # elephant
                if abs(sf - f) == 2 and abs(sr - r) == 2:
                    mf, mr = (sf + f) // 2, (sr + r) // 2
                    if board[mr][mf] is None:
                        # cannot cross river
                        if by == "r" and r <= 4 and sr <= 4:
                            return True
                        if by == "b" and r >= 5 and sr >= 5:
                            return True
            elif kind == "n":  # horse
                df, dr = f - sf, r - sr
                hobble = None
                if (abs(df), abs(dr)) == (1, 2):
                    hobble = (sf, sr + (1 if dr > 0 else -1))
                elif (abs(df), abs(dr)) == (2, 1):
                    hobble = (sf + (1 if df > 0 else -1), sr)
                if hobble is not None:
                    hf, hr = hobble
                    if in_bounds(hf, hr) and board[hr][hf] is None:
                        return True
            elif kind == "r":  # chariot
                if sf == f or sr == r:
                    if _clear_ray(board, sf, sr, f, r):
                        return True
            elif kind == "c":  # cannon
                if sf == f or sr == r:
                    screens = _count_screens(board, sf, sr, f, r)
                    target = board[r][f]
                    if target is None and screens == 0:
                        pass  # move not attack for empty? cannon attacks only with screen
                    if target is not None and screens == 1:
                        return True
            elif kind == "p":
                fwd = 1 if by == "r" else -1
                if sf == f and r == sr + fwd:
                    return True
                crossed = (by == "r" and sr >= 5) or (by == "b" and sr <= 4)
                if crossed and sr == r and abs(sf - f) == 1:
                    return True
    return False


def _clear_ray(board, sf, sr, tf, tr) -> bool:
    if sf == tf:
        lo, hi = sorted((sr, tr))
        return all(board[rr][sf] is None for rr in range(lo + 1, hi))
    if sr == tr:
        lo, hi = sorted((sf, tf))
        return all(board[sr][ff] is None for ff in range(lo + 1, hi))
    return False


def _count_screens(board, sf, sr, tf, tr) -> int:
    n = 0
    if sf == tf:
        lo, hi = sorted((sr, tr))
        for rr in range(lo + 1, hi):
            if board[rr][sf] is not None:
                n += 1
        return n
    if sr == tr:
        lo, hi = sorted((sf, tf))
        for ff in range(lo + 1, hi):
            if board[sr][ff] is not None:
                n += 1
        return n
    return 99


def in_check(board, color: str) -> bool:
    k = find_king(board, color)
    if k is None:
        return True
    return attacked_by(board, k[0], k[1], "b" if color == "r" else "r")


def _apply(board, fr, tr, ff, tf):
    nb = [row[:] for row in board]
    nb[tr][tf] = nb[fr][ff]
    nb[fr][ff] = None
    return nb


def gen_pseudo(board, side: str) -> list[tuple[int, int, int, int]]:
    """Generate pseudo-legal moves as (ff,fr,tf,tr)."""
    out: list[tuple[int, int, int, int]] = []
    for fr in range(10):
        for ff in range(9):
            p = board[fr][ff]
            if not p or p[0] != side:
                continue
            kind = p[1]
            if kind == "k":
                pal = RED_PAL if side == "r" else BLK_PAL
                for df, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    tf, tr = ff + df, fr + dr
                    if (tf, tr) in pal:
                        cap = board[tr][tf]
                        if cap is None or cap[0] != side:
                            out.append((ff, fr, tf, tr))
            elif kind == "a":
                pal = RED_PAL if side == "r" else BLK_PAL
                for df, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    tf, tr = ff + df, fr + dr
                    if (tf, tr) in pal:
                        cap = board[tr][tf]
                        if cap is None or cap[0] != side:
                            out.append((ff, fr, tf, tr))
            elif kind == "b":
                for df, dr in ((2, 2), (2, -2), (-2, 2), (-2, -2)):
                    tf, tr = ff + df, fr + dr
                    if not in_bounds(tf, tr):
                        continue
                    if side == "r" and (fr > 4 or tr > 4):
                        continue
                    if side == "b" and (fr < 5 or tr < 5):
                        continue
                    mf, mr = ff + df // 2, fr + dr // 2
                    if board[mr][mf] is not None:
                        continue
                    cap = board[tr][tf]
                    if cap is None or cap[0] != side:
                        out.append((ff, fr, tf, tr))
            elif kind == "n":
                for df, dr, hf, hr in (
                    (1, 2, 0, 1),
                    (1, -2, 0, -1),
                    (-1, 2, 0, 1),
                    (-1, -2, 0, -1),
                    (2, 1, 1, 0),
                    (2, -1, 1, 0),
                    (-2, 1, -1, 0),
                    (-2, -1, -1, 0),
                ):
                    tf, tr = ff + df, fr + dr
                    if not in_bounds(tf, tr):
                        continue
                    if board[fr + hr][ff + hf] is not None:
                        continue
                    cap = board[tr][tf]
                    if cap is None or cap[0] != side:
                        out.append((ff, fr, tf, tr))
            elif kind == "r":
                for df, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    tf, tr = ff + df, fr + dr
                    while in_bounds(tf, tr):
                        cap = board[tr][tf]
                        if cap is None:
                            out.append((ff, fr, tf, tr))
                        else:
                            if cap[0] != side:
                                out.append((ff, fr, tf, tr))
                            break
                        tf += df
                        tr += dr
            elif kind == "c":
                for df, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    tf, tr = ff + df, fr + dr
                    screens = 0
                    while in_bounds(tf, tr):
                        cap = board[tr][tf]
                        if screens == 0:
                            if cap is None:
                                out.append((ff, fr, tf, tr))
                            else:
                                screens = 1
                        else:
                            if cap is not None:
                                if cap[0] != side:
                                    out.append((ff, fr, tf, tr))
                                break
                        tf += df
                        tr += dr
            elif kind == "p":
                fwd = 1 if side == "r" else -1
                tf, tr = ff, fr + fwd
                if in_bounds(tf, tr):
                    cap = board[tr][tf]
                    if cap is None or cap[0] != side:
                        out.append((ff, fr, tf, tr))
                crossed = (side == "r" and fr >= 5) or (side == "b" and fr <= 4)
                if crossed:
                    for df in (-1, 1):
                        tf, tr = ff + df, fr
                        if in_bounds(tf, tr):
                            cap = board[tr][tf]
                            if cap is None or cap[0] != side:
                                out.append((ff, fr, tf, tr))
    return out


def gen_legal(board, side: str) -> list[tuple[int, int, int, int]]:
    legal = []
    for mv in gen_pseudo(board, side):
        ff, fr, tf, tr = mv
        nb = _apply(board, fr, tr, ff, tf)
        if not facing_ok(nb):
            continue
        if in_check(nb, side):
            continue
        legal.append(mv)
    return legal


def is_mate(board, side: str) -> bool:
    """side to move is checkmated."""
    return in_check(board, side) and not gen_legal(board, side)


def move_str(mv) -> str:
    ff, fr, tf, tr = mv
    return f"{sq_name(ff, fr)}{sq_name(tf, tr)}"


def parse_move(s: str) -> tuple[int, int, int, int]:
    s = s.strip().lower()
    if len(s) != 4:
        raise ValueError(s)
    ff, fr = parse_sq(s[:2])
    tf, tr = parse_sq(s[2:])
    return ff, fr, tf, tr


def crosses_river(mv) -> bool:
    ff, fr, tf, tr = mv
    return (fr <= 4 and tr >= 5) or (fr >= 5 and tr <= 4)


# --- search ---

FORCE_BUDGET = 3  # max Red plies for forced mate
COOP_BUDGET = 3


def _gives_check(board, mv, side: str) -> bool:
    nb = _apply(board, mv[1], mv[3], mv[0], mv[2])
    opp = "b" if side == "r" else "r"
    return is_mate(nb, opp) or in_check(nb, opp)


def _red_candidates(b, rem: int):
    moves = gen_legal(b, "r")
    checks = [m for m in moves if _gives_check(b, m, "r")]
    # Prefer checks; for mate-in-1 discovery also allow all when rem==1
    if rem <= 1:
        return moves
    return checks or moves


def forced_mate_in(board, side: str, budget: int) -> int | None:
    """Shortest forced mate length in Red plies, or None. side is to-move."""
    memo: dict = {}

    def red_to_mate(b, rem: int) -> int | None:
        key = (board_key(b), "r", rem)
        if key in memo:
            return memo[key]
        if rem <= 0:
            memo[key] = None
            return None
        if is_mate(b, "b"):
            memo[key] = 0
            return 0
        best = None
        for mv in _red_candidates(b, rem):
            nb = _apply(b, mv[1], mv[3], mv[0], mv[2])
            if is_mate(nb, "b"):
                best = 1 if best is None else min(best, 1)
                continue
            if rem <= 1:
                continue
            replies = gen_legal(nb, "b")
            if not replies:
                continue
            worst = 0
            ok = True
            for rm in replies:
                nb2 = _apply(nb, rm[1], rm[3], rm[0], rm[2])
                sub = red_to_mate(nb2, rem - 1)
                if sub is None:
                    ok = False
                    break
                worst = max(worst, 1 + sub)
            if ok:
                best = worst if best is None else min(best, worst)
        memo[key] = best
        return best

    if side != "r":
        return None
    return red_to_mate(board, budget)


def help_mate_in(board, side: str, budget: int) -> int | None:
    """Shortest help-mate (both cooperate to mate Black) in Red plies."""
    memo: dict = {}

    def rec(b, turn: str, rem: int) -> int | None:
        key = (board_key(b), turn, rem)
        if key in memo:
            return memo[key]
        if is_mate(b, "b"):
            memo[key] = 0
            return 0
        if rem <= 0:
            memo[key] = None
            return None
        best = None
        if turn == "r":
            for mv in _red_candidates(b, rem):
                nb = _apply(b, mv[1], mv[3], mv[0], mv[2])
                if is_mate(nb, "b"):
                    best = 1 if best is None else min(best, 1)
                    continue
                if rem <= 1:
                    continue
                sub = rec(nb, "b", rem - 1)
                if sub is not None:
                    best = 1 + sub if best is None else min(best, 1 + sub)
                    if best == 1:
                        break
        else:
            moves = gen_legal(b, "b")
            if not moves:
                memo[key] = None
                return None
            # Prefer king moves / captures when cooperating.
            def rank(m):
                ff, fr, tf, tr = m
                piece = b[fr][ff]
                cap = 0 if b[tr][tf] is None else 1
                king = 1 if piece and piece[1] == "k" else 0
                return (-king, -cap)

            for mv in sorted(moves, key=rank):
                nb = _apply(b, mv[1], mv[3], mv[0], mv[2])
                sub = rec(nb, "r", rem)
                if sub is not None:
                    best = sub if best is None else min(best, sub)
                    if best <= 1:
                        break
        memo[key] = best
        return best

    if side != "r":
        return None
    return rec(board, side, budget)


def classify(board, to_move: str = "r"):
    force = forced_mate_in(board, to_move, FORCE_BUDGET)
    helpm = help_mate_in(board, to_move, COOP_BUDGET)
    if force is not None:
        return "win", force, True
    if helpm is not None:
        return "trap", helpm, True
    return "fort", None, False


def threat_moves(board) -> list[str]:
    """Red first moves that threaten mate-next if Black does nothing useful:
    after Red's move, if Black had a pass, Red would mate on next ply —
    i.e. there exists a Red follow-up that mates immediately, AND Black has
    at least one legal reply (so it's not already mate). A move that mates
    immediately is finished mate, not a threat.
    """
    threats = []
    for mv in gen_legal(board, "r"):
        nb = _apply(board, mv[1], mv[3], mv[0], mv[2])
        if is_mate(nb, "b"):
            continue
        # can Red mate on the next Red ply against some Black replies?
        # Threat definition (booklet): after Red try, if Black passes conceptually,
        # Red has a one-move mate. Since no pass: after Red try, there exists a
        # Red move that mates from this position with Black to move having been
        # skipped — equivalent to: from nb with Red to move again, mate in 1.
        # But side to move is Black. So: exists Black "pass" then Red mates —
        # we model as: exists Red move from nb as if Red moved again (illegal).
        # Practical definition matching hex: after Black's best effort to not
        # get mated next... Actually hex: after Black cell, if White does nothing,
        # Black completes on next stone.
        # Analog: after Red move, if Black does nothing, Red mates next.
        # Model "Black does nothing" = leave position with Red to move from nb.
        mate_next = False
        for mv2 in gen_legal(nb, "r"):  # pretend Red moves again — wrong
            pass
        # Correct model: Black has replies; a threat is: there exists a Red
        # follow-up that mates immediately AFTER some specific quiet Black move
        # OR: for every... No — hex says: if White did nothing, Black finishes.
        # So: from position after Red try, treating it as Red-to-move (skip Black),
        # Red has a mating move. Generate Red moves from nb illegally:
        # We check: exists a piece move by Red from nb that would mate if it were Red's turn.
        # Use gen_legal on a copy by temporarily ignoring side — apply Red moves from nb.
        for mv2 in gen_pseudo(nb, "r"):
            nb2 = _apply(nb, mv2[1], mv2[3], mv2[0], mv2[2])
            if not facing_ok(nb2) or in_check(nb2, "r"):
                continue
            if is_mate(nb2, "b"):
                mate_next = True
                break
        if mate_next:
            threats.append(move_str(mv))
    return threats


def find_refutation(board, red_uci: str) -> str | None:
    """Black reply that prevents immediate Red mate-next threat."""
    mv = parse_move(red_uci)
    nb = _apply(board, mv[1], mv[3], mv[0], mv[2])
    for rm in gen_legal(nb, "b"):
        nb2 = _apply(nb, rm[1], rm[3], rm[0], rm[2])
        # After this reply, Red should not have an immediate mate.
        still = False
        for mv2 in gen_legal(nb2, "r"):
            nb3 = _apply(nb2, mv2[1], mv2[3], mv2[0], mv2[2])
            if is_mate(nb3, "b"):
                still = True
                break
        if not still:
            return move_str(rm)
    return None


def winning_first_moves(board) -> list[str]:
    out = []
    force0 = forced_mate_in(board, "r", FORCE_BUDGET)
    if force0 is None:
        return out
    for mv in gen_legal(board, "r"):
        nb = _apply(board, mv[1], mv[3], mv[0], mv[2])
        if is_mate(nb, "b"):
            out.append(move_str(mv))
            continue
        replies = gen_legal(nb, "b")
        if not replies:
            continue
        ok = True
        for rm in replies:
            nb2 = _apply(nb, rm[1], rm[3], rm[0], rm[2])
            if forced_mate_in(nb2, "r", FORCE_BUDGET - 1) is None:
                ok = False
                break
        if ok:
            out.append(move_str(mv))
    return out


def river_cross_in_line(moves: list[str]) -> bool:
    for m in moves:
        # strip side prefixes if present
        tok = m.split()[-1] if " " in m else m
        tok = tok.split("|")[0]
        if len(tok) == 4 and crosses_river(parse_move(tok)):
            return True
    return False
