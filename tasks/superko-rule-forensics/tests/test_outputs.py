"""Verifier for the Weiqi capture tournament card."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ANSWERS_PATH = Path("/app/answers.json")
REFEREE_JAR = Path("/app/bin/judge.jar")
REFEREE_SHA_PATH = Path("/app/bin/judge.jar.sha256")
PUZZLE_DIR = Path("/app/puzzles")

EXPECTED_RULE = "positional_superko"
WIN_BOARDS = (1, 2, 3, 4)
UNWINNABLE_BOARDS = (5, 6, 7, 8, 9, 10, 11, 12)
TRAP_BOARDS = (5, 6, 7, 8, 9, 10, 12)  # coop_capturable + unwinnable
FORT_BOARDS = (11,)
BOARD_COUNT = 12

MIN_BLACK_MOVES = {1: 6, 2: 6, 3: 5, 4: 5}

TRAP_COOP = {
    5: ["black 4,5", "white pass", "black 5,4", "white pass", "black 5,6", "white pass", "black 6,5"],
    6: ["black 3,4", "white pass", "black 4,3", "white pass", "black 4,5", "white pass", "black 5,4"],
    7: ["black 4,6", "white pass", "black 5,5", "white pass", "black 5,7", "white pass", "black 6,6"],
    8: ["black 4,5", "white pass", "black 5,4", "white pass", "black 5,6", "white pass", "black 6,5"],
    9: ["black 4,5", "white pass", "black 5,4", "white pass", "black 5,6", "white pass", "black 6,5"],
    10: ["black 3,5", "white pass", "black 4,4", "white pass", "black 4,6", "white pass", "black 5,5"],
    12: ["black 4,4", "white pass", "black 5,3", "white pass", "black 5,5", "white pass", "black 6,4"],
}


def _load_answers():
    assert ANSWERS_PATH.exists(), f"missing {ANSWERS_PATH}"
    with ANSWERS_PATH.open() as handle:
        return json.load(handle)


def _run_referee(board_id: int, sequence: list[str]) -> dict:
    board_path = PUZZLE_DIR / f"board_{board_id:02d}.txt"
    cmd = [
        "java", "-jar", "/app/bin/judge.jar",
        "validate",
        "--board", str(board_path),
        "--moves", ";".join(sequence),
    ]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, check=False, timeout=60,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"referee exited {proc.returncode} for board {board_id}: "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _parse_grid(final_board: str) -> list[str]:
    rows = [row for row in final_board.splitlines() if row.strip()]
    assert len(rows) == 9 and all(len(r) == 9 for r in rows), final_board
    return rows


def _target_from_puzzle(board_id: int) -> tuple[int, int]:
    text = (PUZZLE_DIR / f"board_{board_id:02d}.txt").read_text()
    for line in text.splitlines():
        if line.startswith("target:"):
            raw = line.split(":", 1)[1].strip()
            r_s, c_s = raw.split(",")
            return int(r_s), int(c_s)
    raise AssertionError(f"no target in board {board_id}")


def _group_libs(grid: list[str], sr: int, sc: int) -> list[tuple[int, int]]:
    color = grid[sr - 1][sc - 1]
    if color == ".":
        return []
    seen = {(sr, sc)}
    stack = [(sr, sc)]
    libs: set[tuple[int, int]] = set()
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (1 <= nr <= 9 and 1 <= nc <= 9) or (nr, nc) in seen:
                continue
            cell = grid[nr - 1][nc - 1]
            if cell == color:
                seen.add((nr, nc))
                stack.append((nr, nc))
            elif cell == ".":
                libs.add((nr, nc))
    return sorted(libs)


def _starting_target_libs(board_id: int) -> list[tuple[int, int]]:
    text = (PUZZLE_DIR / f"board_{board_id:02d}.txt").read_text()
    rows: list[str] = []
    mode = False
    for line in text.splitlines():
        if mode and line.strip():
            rows.append(line.strip())
            if len(rows) == 9:
                break
        if line.strip() == "board:":
            mode = True
    target = _target_from_puzzle(board_id)
    return _group_libs(rows, *target)


@pytest.fixture(scope="module")
def answers():
    return _load_answers()


@pytest.fixture(scope="module")
def boards_by_id(answers):
    return {int(entry["board_id"]): entry for entry in answers["boards"]}


def test_referee_binary_present():
    """Scorer jar must exist."""
    assert REFEREE_JAR.exists()
    assert os.access(REFEREE_JAR, os.R_OK)


def test_referee_binary_integrity():
    """Scorer jar sha256 must match build-time checksum."""
    expected = REFEREE_SHA_PATH.read_text().strip()
    proc = subprocess.run(
        ["sha256sum", "/app/bin/judge.jar"],
        capture_output=True, text=True, check=True, timeout=30,
    )
    actual = proc.stdout.split()[0].strip()
    assert actual == expected


def test_answers_file_valid_shape(answers):
    """answers.json must expose rule, boards 1..12, and coop_capturable."""
    assert set(answers.keys()) >= {"rule", "boards"}
    assert len(answers["boards"]) == BOARD_COUNT
    seen_ids = [int(e["board_id"]) for e in answers["boards"]]
    assert seen_ids == list(range(1, BOARD_COUNT + 1))
    for entry in answers["boards"]:
        assert "coop_capturable" in entry and isinstance(entry["coop_capturable"], bool)
        assert entry["status"] in ("win", "unwinnable")


def test_rule_variant_is_positional_superko(answers):
    """Declared rule must be positional_superko."""
    rule = answers["rule"]
    allowed = {"positional_superko", "situational_superko", "natural_situational_superko"}
    assert rule in allowed
    assert rule == EXPECTED_RULE


@pytest.mark.parametrize("board_id", WIN_BOARDS)
def test_win_board_entry_shape(boards_by_id, board_id):
    """Wins need status, coop_capturable, and a sequence."""
    entry = boards_by_id[board_id]
    assert entry["status"] == "win"
    assert entry["coop_capturable"] is True
    seq = entry.get("sequence")
    assert isinstance(seq, list) and seq
    for move in seq:
        assert move.startswith(("black ", "white "))


@pytest.mark.parametrize("board_id", WIN_BOARDS)
def test_win_board_min_black_plies(boards_by_id, board_id):
    """Win PVs meet irreducible Black-stone floors."""
    seq = boards_by_id[board_id]["sequence"]
    black_plies = sum(1 for m in seq if m.startswith("black ") and m != "black pass")
    assert black_plies >= MIN_BLACK_MOVES[board_id]


@pytest.mark.parametrize("board_id", WIN_BOARDS)
def test_win_board_sequence_captures_target(boards_by_id, board_id):
    """Win sequences empty the target under the scorer."""
    result = _run_referee(board_id, boards_by_id[board_id]["sequence"])
    assert result["all_legal"] and result["target_empty"]


@pytest.mark.parametrize("board_id", WIN_BOARDS)
def test_win_sequence_rejects_cooperative_white_pass(boards_by_id, board_id):
    """Reject cooperative white passes with legal liberty replies."""
    seq = boards_by_id[board_id]["sequence"]
    target = _target_from_puzzle(board_id)
    prefix: list[str] = []
    for move in seq:
        if move == "white pass":
            state = _run_referee(board_id, prefix)
            grid = _parse_grid(state["final_board"])
            libs = _group_libs(grid, *target)
            if len(libs) >= 2:
                legal = False
                for r, c in libs:
                    probe = _run_referee(board_id, prefix + [f"white {r},{c}"])
                    if probe.get("all_legal"):
                        legal = True
                        break
                assert not legal, f"board {board_id}: cooperative white pass at {prefix}"
        prefix.append(move)


@pytest.mark.parametrize("board_id", UNWINNABLE_BOARDS)
def test_unwinnable_board_marked(boards_by_id, board_id):
    """Unwinnable boards carry status unwinnable without sequences."""
    entry = boards_by_id[board_id]
    assert entry["status"] == "unwinnable"
    assert entry.get("sequence") in (None, [],)


@pytest.mark.parametrize("board_id", TRAP_BOARDS)
def test_trap_coop_capturable_true(boards_by_id, board_id):
    """Trap boards are cooperatively capturable."""
    assert boards_by_id[board_id]["coop_capturable"] is True


@pytest.mark.parametrize("board_id", FORT_BOARDS)
def test_fort_coop_capturable_false(boards_by_id, board_id):
    """Fortress boards are not cooperatively capturable."""
    assert boards_by_id[board_id]["coop_capturable"] is False
    assert boards_by_id[board_id].get("refutations") in (None, [],)


@pytest.mark.parametrize("board_id", TRAP_BOARDS)
def test_trap_rejects_win_claims_despite_coop_fill(boards_by_id, board_id):
    """Coop fills empty traps but status stays unwinnable."""
    entry = boards_by_id[board_id]
    coop = TRAP_COOP[board_id]
    result = _run_referee(board_id, coop)
    assert result.get("all_legal") and result.get("target_empty")
    assert entry["status"] == "unwinnable"


@pytest.mark.parametrize("board_id", TRAP_BOARDS)
def test_trap_refutations_cover_every_liberty(boards_by_id, board_id):
    """Trap refutations cover every starting target liberty."""
    entry = boards_by_id[board_id]
    refs = entry.get("refutations")
    assert isinstance(refs, list) and refs
    libs = _starting_target_libs(board_id)
    got = sorted(tuple(map(int, r["after_black"].split(","))) for r in refs)
    assert got == libs, f"board {board_id}: refutations {got} != libs {libs}"
    for ref in refs:
        white = ref["white"]
        wmove = "white pass" if white == "pass" else f"white {white}"
        seq = [f"black {ref['after_black']}", wmove]
        result = _run_referee(board_id, seq)
        assert result.get("all_legal"), f"board {board_id} bad refutation {seq}: {result}"
        assert not result.get("target_empty"), f"board {board_id} refutation emptied target: {seq}"


def test_board11_rejects_naive_eye_fills(boards_by_id):
    """Two-eye fortress rejects short fills."""
    entry = boards_by_id[11]
    for attempt in [
        ["black 5,4"],
        ["black 5,6"],
        ["black 5,4", "white pass", "black 5,6"],
    ]:
        result = _run_referee(11, attempt)
        assert not result.get("target_empty")
    assert entry["status"] == "unwinnable"
    assert entry["coop_capturable"] is False


def test_sensei_hint_false_greens_traps(boards_by_id):
    """Liberty probe false-greens traps that stay unwinnable."""
    proc = subprocess.run(
        ["/app/tools/sensei_hint.sh"],
        capture_output=True, text=True, check=True, timeout=30,
    )
    lines = {line.split()[0]: line for line in proc.stdout.splitlines() if line.strip()}
    for board_id in (5, 6, 7, 9, 10, 12):
        key = f"board_{board_id:02d}"
        assert "looks_fillable_if_white_passes" in lines[key]
        assert boards_by_id[board_id]["status"] == "unwinnable"
        assert boards_by_id[board_id]["coop_capturable"] is True


def test_win_sequences_include_white_resistance(boards_by_id):
    """Win PVs include White stone replies."""
    for board_id in WIN_BOARDS:
        seq = boards_by_id[board_id]["sequence"]
        assert any(m.startswith("white ") and m != "white pass" for m in seq)


def test_win_sequences_have_enough_white_plies(boards_by_id):
    """Deep wins include enough White plies."""
    for board_id, need in ((1, 4), (2, 4), (3, 3)):
        seq = boards_by_id[board_id]["sequence"]
        white_plies = sum(1 for m in seq if m.startswith("white "))
        assert white_plies >= need


def test_all_win_sequences_produce_captures(boards_by_id):
    """Win sequences capture at least one stone."""
    for board_id in WIN_BOARDS:
        result = _run_referee(board_id, boards_by_id[board_id]["sequence"])
        caps = sum(step.get("captured", 0) for step in result["steps"])
        assert caps >= 1


def _run_printer_doctor() -> str:
    proc = subprocess.run(
        ["python3", "-m", "kiosk", "doctor"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
        cwd="/app",
        env={**os.environ, "PYTHONPATH": "/app"},
    )
    return proc.stdout


def _run_printer_emit(path: Path) -> dict:
    subprocess.run(
        ["python3", "-m", "kiosk", "emit", "-o", str(path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
        cwd="/app",
        env={**os.environ, "PYTHONPATH": "/app"},
    )
    with path.open() as handle:
        return json.load(handle)


def test_printer_ko_matches_positional_superko():
    """Overnight printer doctor must report the live positional ko family."""
    out = _run_printer_doctor()
    line = next(ln for ln in out.splitlines() if ln.startswith("printer_ko_guess="))
    assert line.split("=", 1)[1].strip() == EXPECTED_RULE


def test_printer_does_not_promote_trap_coop_to_win():
    """Sensei-green trap rounds stay unwinnable once the printer is aligned."""
    out = _run_printer_doctor()
    line = next(ln for ln in out.splitlines() if ln.startswith("printer_round_5="))
    opinion = json.loads(line.split("=", 1)[1])
    assert opinion["status"] == "unwinnable"
    assert opinion["coop_capturable"] is True


@pytest.mark.parametrize("board_id", TRAP_BOARDS)
def test_printer_refutations_keep_target_with_stone_replies(board_id, tmp_path):
    """Fresh printer emit must file judge-legal White liberty replies."""
    draft = _run_printer_emit(tmp_path / "card.json")
    boards = {int(b["board_id"]): b for b in draft["boards"]}
    entry = boards[board_id]
    assert entry["status"] == "unwinnable"
    assert entry["coop_capturable"] is True
    refs = entry.get("refutations") or []
    assert refs
    libs = _starting_target_libs(board_id)
    got = sorted(tuple(map(int, r["after_black"].split(","))) for r in refs)
    assert got == libs
    stone_replies = sum(1 for r in refs if r["white"] != "pass")
    for ref in refs:
        white = ref["white"]
        wmove = "white pass" if white == "pass" else f"white {white}"
        result = _run_referee(board_id, [f"black {ref['after_black']}", wmove])
        assert result.get("all_legal")
        assert not result.get("target_empty")
    assert stone_replies >= 1


def test_printer_doctor_agrees_with_answers_rule(answers):
    """Printer doctor ko guess must match the handed-in card."""
    out = _run_printer_doctor()
    line = next(ln for ln in out.splitlines() if ln.startswith("printer_ko_guess="))
    assert line.split("=", 1)[1].strip() == answers["rule"]
    assert "printer_round_5=" in out
    assert "unwinnable" in out
