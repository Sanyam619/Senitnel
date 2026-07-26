"""Verifier for the Hex capture contest card.

Independently classifies each round (win / trap / fort) from the round file
with a self-contained Hex link search, then checks the submitted card.
Legality of the cells the card names is confirmed with the sealed judge.jar;
the win/trap/fort verdicts are recomputed here.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

CARD_PATH = Path("/output/hex-card.json")
JUDGE = Path("/app/bin/judge.jar")
JUDGE_SEAL = Path("/opt/tbench/judge.jar")
PUZZLE_DIR = Path("/app/puzzles")
PUZZLE_SEAL = Path("/opt/tbench/puzzles")
SCHEMA_TAG = "hex-shore-v1"

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def cell_name(c, r):
    return f"{chr(ord('a') + c)}{r + 1}"


def read_board(path):
    black, white, rows, in_board = set(), set(), [], False
    for line in path.read_text().splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if t == "board:":
            in_board = True
            continue
        if in_board:
            rows.append(t)
    n = len(rows)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "B":
                black.add((c, r))
            elif ch == "W":
                white.add((c, r))
    return frozenset(black), frozenset(white), n


def _neigh(c, r, n):
    for dc, dr in DIRS:
        nc, nr = c + dc, r + dr
        if 0 <= nc < n and 0 <= nr < n:
            yield nc, nr


def black_linked(black, n):
    stack = [(c, 0) for c in range(n) if (c, 0) in black]
    seen = set(stack)
    while stack:
        c, r = stack.pop()
        if r == n - 1:
            return True
        for nb in _neigh(c, r, n):
            if nb in black and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def coop_fillable(black, white, n):
    stack = [(c, 0) for c in range(n) if (c, 0) not in white]
    seen = set(stack)
    while stack:
        c, r = stack.pop()
        if r == n - 1:
            return True
        for nb in _neigh(c, r, n):
            if nb not in white and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def _cells(n):
    return [(c, r) for r in range(n) for c in range(n)]


def _solve(black, white, side, n):
    memo = {}

    def rec(bl, wh, turn):
        if black_linked(bl, n):
            return True
        key = (bl, wh, turn)
        if key in memo:
            return memo[key]
        occ = bl | wh
        moves = [m for m in _cells(n) if m not in occ]
        if not moves:
            memo[key] = black_linked(bl, n)
            return memo[key]
        if turn == "b":
            res = any(rec(bl | {m}, wh, "w") for m in moves)
        else:
            res = all(rec(bl, wh | {m}, "b") for m in moves)
        memo[key] = res
        return res

    return rec(frozenset(black), frozenset(white), side)


def winning_moves(black, white, n):
    occ = set(black) | set(white)
    out = set()
    for m in _cells(n):
        if m in occ:
            continue
        nb = frozenset(black) | {m}
        if black_linked(nb, n) or _solve(nb, white, "w", n):
            out.add(m)
    return out


def immediate_completions(black, white, n):
    occ = set(black) | set(white)
    out = []
    for d in _cells(n):
        if d in occ:
            continue
        if black_linked(frozenset(black) | {d}, n):
            out.append(d)
    return out


def threat_cells(black, white, n):
    occ = set(black) | set(white)
    out = set()
    for c in _cells(n):
        if c in occ:
            continue
        nb = frozenset(black) | {c}
        if black_linked(nb, n):
            continue
        if immediate_completions(nb, white, n):
            out.add(c)
    return out


def classify(black, white, n):
    if black_linked(black, n):
        return "degenerate"
    if not coop_fillable(black, white, n):
        return "fort"
    if _solve(black, white, "b", n):
        return "win"
    return "trap"


def _round_files():
    return sorted(PUZZLE_SEAL.glob("board_*.txt"))


def _expected():
    out = {}
    for path in _round_files():
        bid = path.name[:-4]
        black, white, n = read_board(path)
        out[bid] = {
            "black": black, "white": white, "n": n,
            "kind": classify(black, white, n),
        }
    return out


def _validate(board_id, moves):
    sheet = PUZZLE_SEAL / f"{board_id}.txt"
    proc = subprocess.run(
        ["java", "-jar", str(JUDGE_SEAL), "validate", "--board", str(sheet),
         "--moves", moves],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge failed on {board_id}: {proc.stderr!r}")
    return json.loads(proc.stdout)


def _probe(board_id, side, cell):
    sheet = PUZZLE_SEAL / f"{board_id}.txt"
    proc = subprocess.run(
        ["java", "-jar", str(JUDGE_SEAL), "probe", "--board", str(sheet),
         "--side", side, "--cell", cell],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge failed on {board_id}: {proc.stderr!r}")
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def card():
    assert CARD_PATH.exists(), f"missing {CARD_PATH}"
    return json.loads(CARD_PATH.read_text())


@pytest.fixture(scope="module")
def rounds_by_id(card):
    return {r["board_id"]: r for r in card["rounds"]}


@pytest.fixture(scope="module")
def expected():
    return _expected()


def test_card_shape(card, expected):
    """Card is tagged and lists every round with the required fields."""
    assert card.get("schema_tag") == SCHEMA_TAG
    ids = [r["board_id"] for r in card["rounds"]]
    assert ids == sorted(expected.keys())
    assert len(ids) == len(set(ids)) == len(expected)
    for r in card["rounds"]:
        assert r["status"] in ("win", "trap", "fort")
        assert r["winning_side"] in ("black", "white")
        assert isinstance(r["coop_fillable"], bool)
        assert isinstance(r.get("key_cells", []), list)
        assert isinstance(r.get("refutations", []), list)


def test_printer_repeats_completed_card(card, tmp_path):
    """Repeated kiosk filing preserves identical completed-card bytes."""
    staged = tmp_path / "hex-card.json"
    staged.write_bytes(CARD_PATH.read_bytes())
    command = ["bash", "/app/kiosk/emit_card.sh", str(staged)]
    first_run = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False
    )
    assert first_run.returncode == 0, first_run.stderr
    first = staged.read_bytes()
    second_run = subprocess.run(
        command, capture_output=True, text=True, timeout=60, check=False
    )
    assert second_run.returncode == 0, second_run.stderr
    assert staged.read_bytes() == first
    assert json.loads(first) == card


def test_judge_seal_unchanged(card):
    """Sealed judge matches the verifier-owned seal copy."""
    assert JUDGE.exists() and JUDGE_SEAL.exists()
    assert JUDGE.read_bytes() == JUDGE_SEAL.read_bytes(), (
        "judge.jar no longer matches the sealed copy - leave it unchanged")
    public = sorted(PUZZLE_DIR.glob("board_*.txt"))
    sealed = sorted(PUZZLE_SEAL.glob("board_*.txt"))
    assert [p.name for p in public] == [p.name for p in sealed]
    assert all(
        a.read_bytes() == b.read_bytes()
        for a, b in zip(public, sealed, strict=True)
    )
    assert not Path("/app/bin/judge.jar.sha256").exists()


def test_status_matches_search(rounds_by_id, expected):
    """Every status/winning_side/coop_fillable matches an independent search."""
    for bid, exp in expected.items():
        entry = rounds_by_id[bid]
        assert entry["status"] == exp["kind"], bid
        want_side = "black" if exp["kind"] == "win" else "white"
        assert entry["winning_side"] == want_side, bid
        assert entry["coop_fillable"] is (exp["kind"] != "fort"), bid


def test_win_key_cells(rounds_by_id, expected):
    """Win rounds name only forced-linking Black first plays, judge-legal."""
    wins = [b for b, e in expected.items() if e["kind"] == "win"]
    assert len(wins) >= 3
    for bid in wins:
        exp = expected[bid]
        wm = {cell_name(*m) for m in winning_moves(exp["black"], exp["white"], exp["n"])}
        entry = rounds_by_id[bid]
        keys = entry.get("key_cells") or []
        assert keys, f"{bid}: win needs at least one key cell"
        assert set(keys) <= wm, (
            f"{bid}: key_cells {sorted(set(keys) - wm)} are not forced-winning")
        assert not (entry.get("refutations") or [])
        for cell in keys:
            probe = _probe(bid, "black", cell)
            assert probe.get("legal") is True, f"{bid}: {cell} not a legal play"


def test_trap_refutation_coverage(rounds_by_id, expected):
    """Trap rounds cover every threatening first play with a legal answer."""
    traps = [b for b, e in expected.items() if e["kind"] == "trap"]
    assert len(traps) >= 4
    for bid in traps:
        exp = expected[bid]
        required = {cell_name(*c) for c in threat_cells(exp["black"], exp["white"], exp["n"])}
        assert required, f"{bid}: trap should expose threats"
        entry = rounds_by_id[bid]
        assert not (entry.get("key_cells") or [])
        refs = entry.get("refutations") or []
        covered = {r["cell"] for r in refs}
        missing = sorted(required - covered)
        assert not missing, f"{bid}: uncovered threats {missing}"
        n = exp["n"]
        for ref in refs:
            c, w = ref["cell"], ref["reply"]
            res = _validate(bid, f"black {c};white {w}")
            assert res["all_legal"], f"{bid}: illegal refutation {c}/{w}"
            assert res["black_linked"] is False
            # White's answer must kill the one-stone link threat.
            black2 = frozenset(exp["black"]) | {(ord(c[0]) - 97, int(c[1:]) - 1)}
            white2 = frozenset(exp["white"]) | {(ord(w[0]) - 97, int(w[1:]) - 1)}
            assert not immediate_completions(black2, white2, n), (
                f"{bid}: reply {w} fails to refute threat {c}")


def test_fort_rows(rounds_by_id, expected):
    """Fort rounds are walled off with no key cells or refutations."""
    forts = [b for b, e in expected.items() if e["kind"] == "fort"]
    assert len(forts) >= 2
    for bid in forts:
        entry = rounds_by_id[bid]
        assert entry["status"] == "fort"
        assert entry["coop_fillable"] is False
        assert not (entry.get("key_cells") or [])
        assert not (entry.get("refutations") or [])
        # Judge confirms White already holds the wall.
        sheet = PUZZLE_SEAL / f"{bid}.txt"
        proc = subprocess.run(
            ["java", "-jar", str(JUDGE_SEAL), "view", "--board", str(sheet)],
            capture_output=True, text=True, timeout=60, check=False)
        assert json.loads(proc.stdout)["white_linked"] is True


def test_sensei_is_not_the_verdict(rounds_by_id, expected):
    """Rounds the surface whisper calls fillable are not all wins."""
    proc = subprocess.run(
        ["bash", "/app/tools/sensei_hint.sh", str(PUZZLE_SEAL)],
        capture_output=True, text=True, timeout=60, check=False)
    linkable_look = {
        line.split()[0]
        for line in proc.stdout.splitlines()
        if line.strip().endswith("looks_fillable_if_uncontested")
    }
    trap_ids = {b for b, e in expected.items() if e["kind"] == "trap"}
    # Every trap looks fillable to the sensei but must be filed as a trap.
    assert trap_ids <= linkable_look
    for bid in trap_ids:
        assert rounds_by_id[bid]["status"] == "trap"
