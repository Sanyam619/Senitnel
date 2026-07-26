"""Verifier for the blindfold capture tournament score card.

Independently classifies each round under the documented five-Black-stone
force budget and White fighting-reply rule, then checks the submitted card.
Legality of tagged lines is confirmed with the sealed judge.jar; force
semantics are checked here (the jar only validates moves/announces).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

FILES = "abcdefgh"

# Verifier-owned sealed copy (not beside the agent-writable /app/bin jar).
JUDGE_SEAL = Path("/opt/tbench/judge.jar")

FORCE_MAX_BLACK = 5
MIN_BLACK_STONES = 3
BOARD_COUNT = 9
WIN_SHEETS = (1, 2, 3, 4)
TRAP_SHEETS = (5, 6, 7, 8)
FORT_SHEET = 9

TRAP_THREATS = {
    5: ["c2c4", "c2d2"],
    6: ["d3d5", "d3e3"],
    7: ["g3f3", "g3g5"],
    8: ["c3c6", "c3d3"],
}


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
    """White fighting replies: check escapes, else mark flights + captures only."""
    moves = legal_moves(sq, "w")
    if in_check(sq, "w"):
        return moves
    ms = find_mark_sq(sq, mark)
    useful: list[tuple[int, int, str | None]] = []
    for fr, to, pr in moves:
        if (ms is not None and fr == ms) or (
            sq[to] is not None and sq[to][0] == "b"
        ):
            useful.append((fr, to, pr))
    return useful


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
        cur: list[str | None], who: str, bleft: int
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
    sq: list[str | None], side: str, mark: str, max_black: int = FORCE_MAX_BLACK
) -> list[tuple[str, str]] | None:
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
        cur: list[str | None], who: str, bleft: int
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
    for budget in range(1, max_black + 1):
        got = _coop_at_budget(sq, side, mark, budget)
        if got is not None:
            return got
    return None


ANSWERS_PATH = Path("/app/answers.json")
JUDGE = Path("/app/bin/judge.jar")
SHEET_DIR = Path("/app/puzzles")
JUDGE_CMD = ["java", "-jar", str(JUDGE)]


def _load_answers():
    assert ANSWERS_PATH.exists(), f"missing {ANSWERS_PATH}"
    with ANSWERS_PATH.open() as handle:
        return json.load(handle)


def _run_validate(board_id: int, sequence: list[str]) -> dict:
    sheet = SHEET_DIR / f"board_{board_id:02d}.txt"
    line = ";".join(sequence)
    proc = subprocess.run(
        [*JUDGE_CMD, "validate", "--board", str(sheet), "--moves", line],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge exited {proc.returncode} for sheet {board_id}: "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _announce_line(board_id: int, color_uci_pairs: list[tuple[str, str]]) -> list[str]:
    segs: list[str] = []
    for color, uci in color_uci_pairs:
        if uci == "pass":
            segs.append(f"{color} pass|silent")
            continue
        candidates = ["silent", "check", "mate"]
        if len(uci) >= 4 and uci != "pass":
            candidates.append(f"taken:{uci[2:4]}")
            candidates.append(f"taken:{uci[2:4]}+check")
            candidates.append(f"taken:{uci[2:4]}+mate")
        ok = False
        for ann in candidates:
            trial = segs + [f"{color} {uci}|{ann}"]
            proc = subprocess.run(
                [
                    *JUDGE_CMD,
                    "validate",
                    "--board",
                    str(SHEET_DIR / f"board_{board_id:02d}.txt"),
                    "--moves",
                    ";".join(trial),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.returncode != 0 or not proc.stdout:
                continue
            data = json.loads(proc.stdout)
            if data.get("all_legal"):
                segs = trial
                ok = True
                break
        assert ok, f"could not tag {color} {uci} after {segs}"
    return segs


def _parse_seq_pairs(seq: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for move in seq:
        left = move.split("|", 1)[0].strip()
        color, uci = left.split(None, 1)
        pairs.append((color, uci))
    return pairs


def _uci_of(m: tuple) -> str:
    return to_uci(*m)


def _assert_forcing_sequence(
    sq: list[str | None],
    side: str,
    mark: str,
    pairs: list[tuple[str, str]],
    max_black: int = FORCE_MAX_BLACK,
) -> None:
    """Reject cooperative PVs: every White fighting reply must stay winnable."""
    black_left = max_black
    cur_sq, cur_side = sq, side
    for color, uci in pairs:
        assert color[0] == cur_side, (color, cur_side, uci)
        if mark not in cur_sq:
            break
        if cur_side == "b":
            if uci != "pass":
                assert black_left > 0, "exceeded five-Black-stone force budget"
                black_left -= 1
            got = apply_uci(cur_sq, cur_side, uci)
            assert got is not None, ("illegal black", uci)
            cur_sq, cur_side = got
            if mark not in cur_sq:
                continue
            useful = white_useful(cur_sq, mark)
            if not useful:
                continue
            for m in useful:
                nsq = apply_move(cur_sq, "w", *m)
                assert nsq is not None
                assert _force_at_budget(nsq, "b", mark, black_left) is not None, (
                    f"after black {uci}, white {_uci_of(m)} breaks the force "
                    f"with {black_left} Black stones left"
                )
        else:
            useful = white_useful(cur_sq, mark)
            if useful:
                assert uci != "pass", "cooperative pass while fighting replies exist"
                assert uci in {_uci_of(m) for m in useful}, (
                    f"white {uci} not among fighting replies"
                )
            else:
                assert uci == "pass"
            got = apply_uci(cur_sq, cur_side, uci)
            assert got is not None, ("illegal white", uci)
            cur_sq, cur_side = got
    assert mark not in cur_sq, "sequence does not capture the marked piece"


@pytest.fixture(scope="module")
def answers():
    return _load_answers()


@pytest.fixture(scope="module")
def boards_by_id(answers):
    return {int(entry["board_id"]): entry for entry in answers["boards"]}


@pytest.fixture(scope="module")
def expected_by_id():
    """Independent force/coop classification under the documented budget."""
    out = {}
    for board_id in range(1, BOARD_COUNT + 1):
        sq, side, mark, _t = load_sheet(SHEET_DIR / f"board_{board_id:02d}.txt")
        forced = force_capture(sq, side, mark, max_black=FORCE_MAX_BLACK)
        coop = coop_capture(sq, side, mark, max_black=8)
        if forced is not None:
            out[board_id] = ("win", True)
        elif coop is None:
            out[board_id] = ("unwinnable", False)
        else:
            out[board_id] = ("unwinnable", True)
    return out


def test_k3_zircon(answers):
    """Score card exposes boards 1..N with required fields."""
    assert "boards" in answers
    assert len(answers["boards"]) == BOARD_COUNT
    ids = [int(e["board_id"]) for e in answers["boards"]]
    assert ids == list(range(1, BOARD_COUNT + 1))
    for entry in answers["boards"]:
        assert "coop_capturable" in entry and isinstance(entry["coop_capturable"], bool)
        assert entry["status"] in ("win", "unwinnable")


def test_m8_obsidian(answers):
    """Sealed judge matches the verifier-owned seal copy; card is complete."""
    assert JUDGE.exists()
    assert JUDGE_SEAL.exists()
    assert JUDGE.read_bytes() == JUDGE_SEAL.read_bytes(), (
        "judge.jar no longer matches the sealed copy — leave it unchanged"
    )
    # Adjacent writable checksum files must not be the integrity source.
    assert not Path("/app/bin/judge.jar.sha256").exists()
    assert "boards" in answers
    assert len(answers["boards"]) == BOARD_COUNT


def test_p2_garnet(boards_by_id, expected_by_id):
    """Win sheets carry judge-legal forcing lines under fighting replies."""
    for board_id in WIN_SHEETS:
        assert expected_by_id[board_id][0] == "win"
        entry = boards_by_id[board_id]
        assert entry["status"] == "win"
        assert entry["coop_capturable"] is True
        seq = entry.get("sequence")
        assert isinstance(seq, list) and seq
        for move in seq:
            assert "|" in move
            assert move.startswith(("black ", "white "))
        black_stones = sum(
            1 for m in seq if m.startswith("black ") and " pass|" not in m
        )
        assert black_stones >= MIN_BLACK_STONES
        assert black_stones <= FORCE_MAX_BLACK
        assert any("white " in m and " pass|" not in m for m in seq)
        result = _run_validate(board_id, seq)
        assert result["all_legal"]
        assert result.get("target_captured") or result.get("target_empty")

        sq, side, mark, _t = load_sheet(SHEET_DIR / f"board_{board_id:02d}.txt")
        pairs = _parse_seq_pairs(seq)
        _assert_forcing_sequence(sq, side, mark, pairs, max_black=FORCE_MAX_BLACK)


def test_q7_topaz(boards_by_id, expected_by_id):
    """Trap sheets are unwinnable within budget, cooperatively capturable."""
    for board_id in TRAP_SHEETS:
        assert expected_by_id[board_id] == ("unwinnable", True)
        entry = boards_by_id[board_id]
        assert entry["status"] == "unwinnable"
        assert entry["coop_capturable"] is True
        refs = entry.get("refutations")
        assert isinstance(refs, list) and refs
        covered = {r["after_black"] for r in refs}
        required = set(TRAP_THREATS[board_id])
        missing = sorted(required - covered)
        assert not missing, (
            f"sheet {board_id}: missing required threat refutations {missing}; "
            f"have {sorted(covered)}"
        )
        for ref in refs:
            btry = ref["after_black"]
            white = ref["white"]
            pairs = [("black", btry), ("white", white)]
            segs = _announce_line(board_id, pairs)
            res = _run_validate(board_id, segs)
            assert res["all_legal"]
            assert not (res.get("target_captured") or res.get("target_empty"))


def test_r1_onyx(boards_by_id, expected_by_id):
    """Fort sheet is unwinnable and not cooperatively capturable."""
    assert expected_by_id[FORT_SHEET] == ("unwinnable", False)
    entry = boards_by_id[FORT_SHEET]
    assert entry["status"] == "unwinnable"
    assert entry["coop_capturable"] is False
    assert entry.get("refutations") in (None, [])


def test_t6_amber(boards_by_id):
    """Card rejects sensei fillability stamps on trap rounds."""
    for board_id in TRAP_SHEETS:
        entry = boards_by_id[board_id]
        assert entry["status"] == "unwinnable"
        assert entry["coop_capturable"] is True
        assert entry.get("sequence") in (None, [], ())


def test_v4_jade(boards_by_id):
    """Win sequences use square-tagged capture announces (incl. +check compounds)."""
    for board_id in WIN_SHEETS:
        seq = boards_by_id[board_id]["sequence"]
        taken = [m for m in seq if "|taken:" in m]
        assert taken, f"sheet {board_id} missing taken:<sq> announce"
        for m in taken:
            tag = m.split("|", 1)[1]
            assert tag.startswith("taken:")
            # Compound forms are taken:<sq>, taken:<sq>+check, taken:<sq>+mate
            body = tag[len("taken:") :]
            assert len(body) >= 2
        result = _run_validate(board_id, seq)
        assert result["all_legal"]


def test_w9_flint(boards_by_id):
    """Deep wins include enough White plies of resistance."""
    for board_id in WIN_SHEETS:
        seq = boards_by_id[board_id]["sequence"]
        white_plies = sum(1 for m in seq if m.startswith("white "))
        assert white_plies >= 2


def test_x2_status_matches_independent_search(boards_by_id, expected_by_id):
    """Every round status matches independent force/coop search under the budget."""
    for board_id, (status, coop) in expected_by_id.items():
        entry = boards_by_id[board_id]
        assert entry["status"] == status
        assert entry["coop_capturable"] is coop
