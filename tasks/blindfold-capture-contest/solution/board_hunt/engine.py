"""Judge-mirrored move gen and capture search for the contest oracle."""

from __future__ import annotations

from pathlib import Path

FILES = "abcdefgh"


def parse_sq(s: str) -> int:
    return (ord(s[1]) - ord("1")) * 8 + (ord(s[0]) - ord("a"))


def sq_name(i: int) -> str:
    return f"{FILES[i % 8]}{i // 8 + 1}"


def load_sheet(path: Path) -> tuple[list[str | None], str, str, int]:
    text = path.read_text()
    to_move = "b"
    target: int | None = None
    rows: list[str] = []
    in_board = False
    for line in text.splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if t.startswith("to_move:"):
            to_move = "b" if "black" in t.lower() else "w"
        elif t.startswith("target:"):
            target = parse_sq(t.split(":", 1)[1].strip())
        elif t == "board:":
            in_board = True
        elif in_board and len(t) == 8:
            rows.append(t)
            if len(rows) == 8:
                in_board = False
    if target is None or len(rows) != 8:
        raise ValueError(f"bad sheet {path}")
    sq: list[str | None] = [None] * 64
    for ri, row in enumerate(rows):
        rank = 7 - ri
        for file, ch in enumerate(row):
            if ch == ".":
                continue
            color = "w" if ch.isupper() else "b"
            sq[rank * 8 + file] = color + ch.lower()
    mark = sq[target]
    if mark is None:
        raise ValueError(f"empty target in {path}")
    return sq, to_move, mark, target


def king_sq(sq: list[str | None], c: str) -> int | None:
    for i, p in enumerate(sq):
        if p and p[0] == c and p[1] == "k":
            return i
    return None


def attacked(sq: list[str | None], sq_idx: int, by: str) -> bool:
    tf, tr = sq_idx % 8, sq_idx // 8
    d = 1 if by == "w" else -1
    for df in (-1, 1):
        f, r = tf + df, tr - d
        if 0 <= f < 8 and 0 <= r < 8:
            p = sq[r * 8 + f]
            if p and p[0] == by and p[1] == "p":
                return True
    for df, dr in (
        (1, 2),
        (2, 1),
        (2, -1),
        (1, -2),
        (-1, -2),
        (-2, -1),
        (-2, 1),
        (-1, 2),
    ):
        f, r = tf + df, tr + dr
        if 0 <= f < 8 and 0 <= r < 8:
            p = sq[r * 8 + f]
            if p and p[0] == by and p[1] == "n":
                return True
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            f, r = tf + df, tr + dr
            if 0 <= f < 8 and 0 <= r < 8:
                p = sq[r * 8 + f]
                if p and p[0] == by and p[1] == "k":
                    return True
    for df, dr, need in (
        (1, 0, "r"),
        (-1, 0, "r"),
        (0, 1, "r"),
        (0, -1, "r"),
        (1, 1, "b"),
        (1, -1, "b"),
        (-1, 1, "b"),
        (-1, -1, "b"),
    ):
        f, r = tf + df, tr + dr
        while 0 <= f < 8 and 0 <= r < 8:
            p = sq[r * 8 + f]
            if p:
                if p[0] == by and (p[1] == "q" or p[1] == need):
                    return True
                break
            f += df
            r += dr
    return False


def in_check(sq: list[str | None], c: str) -> bool:
    k = king_sq(sq, c)
    return k is not None and attacked(sq, k, "b" if c == "w" else "w")


def gen(sq: list[str | None], side: str) -> list[tuple[int, int, str | None]]:
    out: list[tuple[int, int, str | None]] = []
    for fr, pc in enumerate(sq):
        if not pc or pc[0] != side:
            continue
        ff, frr = fr % 8, fr // 8
        kind = pc[1]
        if kind == "p":
            d = 1 if side == "w" else -1
            start = 1 if side == "w" else 6
            promo_r = 7 if side == "w" else 0
            r1 = frr + d
            if 0 <= r1 < 8 and sq[r1 * 8 + ff] is None:
                to = r1 * 8 + ff
                if r1 == promo_r:
                    for pr in "qrbn":
                        out.append((fr, to, pr))
                else:
                    out.append((fr, to, None))
                    if frr == start:
                        r2 = frr + 2 * d
                        if 0 <= r2 < 8 and sq[r2 * 8 + ff] is None:
                            out.append((fr, r2 * 8 + ff, None))
            for df in (-1, 1):
                f, r = ff + df, frr + d
                if 0 <= f < 8 and 0 <= r < 8:
                    to = r * 8 + f
                    cap = sq[to]
                    if cap and cap[0] != side:
                        if r == promo_r:
                            for pr in "qrbn":
                                out.append((fr, to, pr))
                        else:
                            out.append((fr, to, None))
        elif kind == "n":
            for df, dr in (
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
            ):
                f, r = ff + df, frr + dr
                if 0 <= f < 8 and 0 <= r < 8:
                    to = r * 8 + f
                    cap = sq[to]
                    if cap is None or cap[0] != side:
                        out.append((fr, to, None))
        elif kind == "k":
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    f, r = ff + df, frr + dr
                    if 0 <= f < 8 and 0 <= r < 8:
                        to = r * 8 + f
                        cap = sq[to]
                        if cap is None or cap[0] != side:
                            out.append((fr, to, None))
        else:
            dirs = {
                "b": ((1, 1), (1, -1), (-1, 1), (-1, -1)),
                "r": ((1, 0), (-1, 0), (0, 1), (0, -1)),
                "q": (
                    (1, 0),
                    (-1, 0),
                    (0, 1),
                    (0, -1),
                    (1, 1),
                    (1, -1),
                    (-1, 1),
                    (-1, -1),
                ),
            }[kind]
            for df, dr in dirs:
                f, r = ff + df, frr + dr
                while 0 <= f < 8 and 0 <= r < 8:
                    to = r * 8 + f
                    cap = sq[to]
                    if cap is not None:
                        if cap[0] != side:
                            out.append((fr, to, None))
                        break
                    out.append((fr, to, None))
                    f += df
                    r += dr
    return out


def apply_move(
    sq: list[str | None], side: str, fr: int, to: int, promo: str | None
) -> list[str | None] | None:
    nsq = sq[:]
    pc = nsq[fr]
    assert pc is not None
    if promo:
        pc = pc[0] + promo
    nsq[to] = pc
    nsq[fr] = None
    if in_check(nsq, side):
        return None
    return nsq


def legal_moves(
    sq: list[str | None], side: str
) -> list[tuple[int, int, str | None]]:
    return [m for m in gen(sq, side) if apply_move(sq, side, *m) is not None]


def to_uci(fr: int, to: int, promo: str | None = None) -> str:
    return sq_name(fr) + sq_name(to) + (promo or "")


def find_mark_sq(sq: list[str | None], mark: str) -> int | None:
    for i, p in enumerate(sq):
        if p == mark:
            return i
    return None


def white_useful(
    sq: list[str | None], mark: str
) -> list[tuple[int, int, str | None]]:
    """White fighting replies: check escapes, else mark flights + captures only.

    Pass is allowed only when this set is empty. King shuffles that are not
    captures are not fighting replies.
    """
    moves = legal_moves(sq, "w")
    if in_check(sq, "w"):
        return moves
    ms = find_mark_sq(sq, mark)
    useful: list[tuple[int, int, str | None]] = []
    for fr, to, pr in moves:
        if ms is not None and fr == ms or sq[to] is not None and sq[to][0] == "b":
            useful.append((fr, to, pr))
    return useful


def order_black(
    sq: list[str | None], mark: str, moves: list[tuple[int, int, str | None]]
) -> list[tuple[int, int, str | None]]:
    cap: list[tuple[int, int, str | None]] = []
    other: list[tuple[int, int, str | None]] = []
    for m in moves:
        nsq = apply_move(sq, "b", *m)
        if nsq is not None and mark not in nsq:
            cap.append(m)
        else:
            other.append(m)
    return cap + other


def _force_at_budget(
    sq: list[str | None], side: str, mark: str, budget: int
) -> list[tuple[str, str]] | None:
    memo: dict = {}

    def rec(
        cur: list[str | None], who: str, bleft: int, memo: dict = memo
    ) -> tuple[bool, list[tuple[str, str]] | None]:
        key = (tuple(cur), who, bleft)
        if key in memo:
            return memo[key]
        if mark not in cur:
            memo[key] = (True, [])
            return memo[key]
        if who == "b":
            if bleft <= 0:
                memo[key] = (False, None)
                return memo[key]
            best: list[tuple[str, str]] | None = None
            for m in order_black(cur, mark, legal_moves(cur, "b")):
                nsq = apply_move(cur, "b", *m)
                assert nsq is not None
                ok, pv = rec(nsq, "w", bleft - 1)
                if ok and pv is not None:
                    cand = [("black", to_uci(*m))] + pv
                    if best is None or len(cand) < len(best):
                        best = cand
                    if mark not in nsq:
                        break
            memo[key] = (best is not None, best)
            return memo[key]
        useful = white_useful(cur, mark)
        if not useful:
            ok, pv = rec(cur, "b", bleft)
            memo[key] = (
                ok,
                ([("white", "pass")] + pv) if ok and pv is not None else None,
            )
            return memo[key]
        first: list[tuple[str, str]] | None = None
        for m in useful:
            nsq = apply_move(cur, "w", *m)
            assert nsq is not None
            ok, pv = rec(nsq, "b", bleft)
            if not ok or pv is None:
                memo[key] = (False, None)
                return memo[key]
            if first is None:
                first = [("white", to_uci(*m))] + pv
        memo[key] = (True, first)
        return memo[key]

    ok, pv = rec(sq, side, budget)
    return pv if ok and pv is not None else None


def force_capture(
    sq: list[str | None], side: str, mark: str, max_black: int = 5
) -> list[tuple[str, str]] | None:
    """AND-OR search: Black exists, White universal over useful replies."""
    for budget in range(1, max_black + 1):
        got = _force_at_budget(sq, side, mark, budget)
        if got is not None:
            return got
    return None


def _coop_at_budget(
    sq: list[str | None], side: str, mark: str, budget: int
) -> list[tuple[str, str]] | None:
    memo: dict = {}

    def rec(
        cur: list[str | None], who: str, bleft: int, memo: dict = memo
    ) -> list[tuple[str, str]] | None:
        key = (tuple(cur), who, bleft)
        if key in memo:
            return memo[key]
        if mark not in cur:
            memo[key] = []
            return []
        if who == "w":
            rest = rec(cur, "b", bleft)
            memo[key] = None if rest is None else [("white", "pass")] + rest
            return memo[key]
        if bleft <= 0:
            memo[key] = None
            return None
        for m in order_black(cur, mark, legal_moves(cur, "b")):
            nsq = apply_move(cur, "b", *m)
            assert nsq is not None
            rest = rec(nsq, "w", bleft - 1)
            if rest is not None:
                memo[key] = [("black", to_uci(*m))] + rest
                return memo[key]
        memo[key] = None
        return None

    return rec(sq, side, budget)


def coop_capture(
    sq: list[str | None], side: str, mark: str, max_black: int = 8
) -> list[tuple[str, str]] | None:
    """White always passes; can Black still remove the mark?"""
    for budget in range(1, max_black + 1):
        got = _coop_at_budget(sq, side, mark, budget)
        if got is not None:
            return got
    return None


def apply_uci(
    sq: list[str | None], side: str, uci: str
) -> tuple[list[str | None], str] | None:
    if uci in ("pass", "0000"):
        return sq[:], ("b" if side == "w" else "w")
    if len(uci) < 4:
        return None
    fr = parse_sq(uci[:2])
    to = parse_sq(uci[2:4])
    promo = uci[4] if len(uci) > 4 else None
    nsq = apply_move(sq, side, fr, to, promo)
    if nsq is None:
        return None
    return nsq, ("b" if side == "w" else "w")


def threat_tries(sq: list[str | None], mark: str) -> list[str]:
    """Black first-tries that capture next move if White passes (not immediate cap)."""
    threats: list[str] = []
    for m in legal_moves(sq, "b"):
        nsq = apply_move(sq, "b", *m)
        assert nsq is not None
        if mark not in nsq:
            # Immediate capture — not a refutation row (piece already gone).
            continue
        # White passes
        after_pass = nsq
        for m2 in legal_moves(after_pass, "b"):
            n2 = apply_move(after_pass, "b", *m2)
            if n2 is not None and mark not in n2:
                threats.append(to_uci(*m))
                break
    return sorted(set(threats))


def refute_threat(
    sq: list[str | None], mark: str, black_uci: str
) -> str | None:
    """Pick a White useful reply that keeps the mark on the board."""
    got = apply_uci(sq, "b", black_uci)
    if got is None:
        return None
    mid, _ = got
    if mark not in mid:
        return None
    useful = white_useful(mid, mark)
    candidates: list[tuple[str, list[str | None]]] = []
    if useful:
        for m in useful:
            nsq = apply_move(mid, "w", *m)
            if nsq is not None and mark in nsq:
                candidates.append((to_uci(*m), nsq))
    else:
        candidates.append(("pass", mid))
    for uci, _nsq in candidates:
        return uci
    # Fall back: any legal white move that keeps the mark
    for m in legal_moves(mid, "w"):
        nsq = apply_move(mid, "w", *m)
        if nsq is not None and mark in nsq:
            return to_uci(*m)
    return "pass" if mark in mid else None
