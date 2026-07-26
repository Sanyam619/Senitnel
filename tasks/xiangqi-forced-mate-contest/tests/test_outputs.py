"""Verifier for the Xiangqi forced-mate contest card.

Independently classifies each round (win / trap / fort) from the sealed
puzzle sheets, then checks the submitted card. Legality of filed lines and
refutations is confirmed with the sealed judge.jar.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import xqlib as xq

CARD_PATH = Path("/output/xiangqi-card.json")
JUDGE = Path("/app/bin/judge.jar")
JUDGE_SEAL = Path("/opt/tbench/judge.jar")
PUZZLE_DIR = Path("/app/puzzles")
PUZZLE_SEAL = Path("/opt/tbench/puzzles")
SCHEMA_TAG = "xiangqi-mate-v1"
FORCE_BUDGET = xq.FORCE_BUDGET

_apply = xq._apply


def _round_files():
    return sorted(PUZZLE_SEAL.glob("board_*.txt"))


def _expected():
    out = {}
    for path in _round_files():
        bid = path.stem
        board, _ = xq.load_sheet(str(path))
        kind, mi, coop = xq.classify(board)
        # Tuple: board, status, mate_in, coop_mate, threat-set
        out[bid] = (
            board,
            kind,
            int(mi or 0),
            bool(coop) if kind != "fort" else False,
            set(xq.threat_moves(board)) if kind == "trap" else set(),
        )
    return out


def _validate(board_id: str, moves: str):
    sheet = PUZZLE_SEAL / f"{board_id}.txt"
    proc = subprocess.run(
        [
            "java",
            "-jar",
            str(JUDGE_SEAL),
            "validate",
            "--board",
            str(sheet),
            "--moves",
            moves,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge failed on {board_id}: {proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _probe(board_id: str, side: str, move: str):
    sheet = PUZZLE_SEAL / f"{board_id}.txt"
    proc = subprocess.run(
        [
            "java",
            "-jar",
            str(JUDGE_SEAL),
            "probe",
            "--board",
            str(sheet),
            "--side",
            side,
            "--move",
            move,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge failed on {board_id}: {proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _line_is_forcing(board, sequence: list[str], budget: int) -> bool:
    """Replay sequence and require forcing replies at each Red ply."""
    b = [row[:] for row in board]
    red_left = budget
    for step in sequence:
        parts = step.split()
        assert len(parts) == 2, step
        side, uci = parts
        mv = xq.parse_move(uci)
        legal = {xq.move_str(m): m for m in xq.gen_legal(b, "r" if side == "red" else "b")}
        assert uci in legal, f"illegal step {step}"
        b = _apply(b, mv[1], mv[3], mv[0], mv[2])
        if side == "red":
            red_left -= 1
            if xq.is_mate(b, "b"):
                return True
            # Every Black reply must still be forced-mateable.
            replies = xq.gen_legal(b, "b")
            assert replies, "no black replies mid-line"
            for rm in replies:
                nb = _apply(b, rm[1], rm[3], rm[0], rm[2])
                if xq.forced_mate_in(nb, "r", red_left) is None:
                    return False
    return xq.is_mate(b, "b")


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
        assert isinstance(r["mate_in"], int)
        assert isinstance(r["river_cross"], bool)
        assert isinstance(r["coop_mate"], bool)
        assert isinstance(r.get("sequence", []), list)
        assert isinstance(r.get("refutations", []), list)


def test_printer_repeats_completed_card(card, tmp_path):
    """Repeated kiosk filing preserves identical completed-card bytes."""
    staged = tmp_path / "xiangqi-card.json"
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


def test_judge_and_puzzles_sealed(card):
    """Sealed judge and puzzle sheets match verifier-owned copies."""
    assert JUDGE.exists() and JUDGE_SEAL.exists()
    assert JUDGE.read_bytes() == JUDGE_SEAL.read_bytes(), (
        "judge.jar no longer matches the sealed copy — leave it unchanged"
    )
    public = sorted(PUZZLE_DIR.glob("board_*.txt"))
    sealed = sorted(PUZZLE_SEAL.glob("board_*.txt"))
    assert [p.name for p in public] == [p.name for p in sealed]
    assert all(
        a.read_bytes() == b.read_bytes()
        for a, b in zip(public, sealed, strict=True)
    )
    assert not Path("/app/bin/judge.jar.sha256").exists()


def test_status_matches_search(rounds_by_id, expected):
    """Every status/coop_mate/mate_in matches an independent search."""
    wins = [b for b, e in expected.items() if e[1] == "win"]
    traps = [b for b, e in expected.items() if e[1] == "trap"]
    forts = [b for b, e in expected.items() if e[1] == "fort"]
    assert len(wins) >= 3 and len(traps) >= 4 and len(forts) >= 2
    for bid, exp in expected.items():
        entry = rounds_by_id[bid]
        _board, want_status, want_mate_in, want_coop, _th = exp
        assert entry["status"] == want_status, bid
        assert entry["coop_mate"] is want_coop, bid
        assert entry["mate_in"] == want_mate_in, bid


def test_win_sequences_forcing_and_exact(rounds_by_id, expected):
    """Win rows file judge-legal forcing lines with exact mate_in and river flag."""
    wins = [b for b, e in expected.items() if e[1] == "win"]
    assert len(wins) >= 3
    for bid in wins:
        board, _st, want_mate_in, _cm, _th = expected[bid]
        entry = rounds_by_id[bid]
        seq = entry.get("sequence") or []
        assert seq, f"{bid}: win needs a sequence"
        assert not (entry.get("refutations") or [])
        assert entry["mate_in"] == want_mate_in
        assert 1 <= entry["mate_in"] <= FORCE_BUDGET
        red_plies = sum(1 for s in seq if s.startswith("red "))
        assert red_plies == entry["mate_in"], (
            f"{bid}: sequence red plies {red_plies} != mate_in {entry['mate_in']}"
        )
        moves = ";".join(seq)
        res = _validate(bid, moves)
        assert res["all_legal"] is True, bid
        assert res["black_mated"] is True, bid
        assert res.get("river_cross") is entry["river_cross"], bid
        assert _line_is_forcing(board, seq, FORCE_BUDGET), (
            f"{bid}: sequence is not forcing under best defense"
        )
        # Padding / detour rejected: shorter forced mate must not be overstated.
        shorter = xq.forced_mate_in(board, "r", entry["mate_in"] - 1)
        assert shorter is None


def test_trap_refutation_coverage(rounds_by_id, expected):
    """Trap rounds cover every threatening first try with a legal answer."""
    traps = [b for b, e in expected.items() if e[1] == "trap"]
    assert len(traps) >= 4
    for bid in traps:
        board, _st, _mi, _cm, required = expected[bid]
        assert required, f"{bid}: trap should expose threats"
        entry = rounds_by_id[bid]
        assert not (entry.get("sequence") or [])
        refs = entry.get("refutations") or []
        covered = {r["move"] for r in refs}
        missing = sorted(required - covered)
        assert not missing, f"{bid}: uncovered threats {missing}"
        for ref in refs:
            red_try, reply = ref["move"], ref["reply"]
            res = _validate(bid, f"red {red_try};black {reply}")
            assert res["all_legal"], f"{bid}: illegal refutation {red_try}/{reply}"
            assert res["black_mated"] is False
            # Reply must kill the one-ply mate threat.
            mv = xq.parse_move(red_try)
            nb = _apply(board, mv[1], mv[3], mv[0], mv[2])
            rm = xq.parse_move(reply)
            nb2 = _apply(nb, rm[1], rm[3], rm[0], rm[2])
            still = False
            for mv2 in xq.gen_legal(nb2, "r"):
                nb3 = _apply(nb2, mv2[1], mv2[3], mv2[0], mv2[2])
                if xq.is_mate(nb3, "b"):
                    still = True
                    break
            assert not still, f"{bid}: reply {reply} fails to refute {red_try}"


def test_fort_rows(rounds_by_id, expected):
    """Fort rounds stay cooperatively unwinnable with empty sequences/refs."""
    forts = [b for b, e in expected.items() if e[1] == "fort"]
    assert len(forts) >= 2
    for bid in forts:
        entry = rounds_by_id[bid]
        assert entry["status"] == "fort"
        assert entry["coop_mate"] is False
        assert entry["mate_in"] == 0
        assert entry["river_cross"] is False
        assert not (entry.get("sequence") or [])
        assert not (entry.get("refutations") or [])


def test_sensei_is_not_the_verdict(rounds_by_id, expected):
    """Rounds the surface whisper calls mateable are not all wins."""
    proc = subprocess.run(
        ["bash", "/app/tools/sensei_hint.sh", str(PUZZLE_SEAL)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    cheerful = {
        line.split()[0]
        for line in proc.stdout.splitlines()
        if line.strip().endswith("looks_mateable_if_uncontested")
    }
    trap_ids = {b for b, e in expected.items() if e[1] == "trap"}
    assert trap_ids <= cheerful, (
        f"sensei should call every trap mateable; missed {sorted(trap_ids - cheerful)}"
    )
    for bid in trap_ids:
        assert rounds_by_id[bid]["status"] == "trap"


def test_illegal_palace_draft_rejected(rounds_by_id, expected):
    """Kiosk-style illegal palace steps fail the sealed judge."""
    # Advisor step outside the palace must be illegal on a live sheet.
    sample = next(iter(expected))
    probe = _probe(sample, "red", "d0c1")
    assert probe.get("legal") is False
    wins = [b for b, e in expected.items() if e[1] == "win"]
    for bid in wins:
        for step in rounds_by_id[bid].get("sequence") or []:
            assert "d0c1" not in step
