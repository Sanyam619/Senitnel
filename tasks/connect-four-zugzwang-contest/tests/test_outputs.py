"""Verifier for the Connect Four zugzwang booklet.

Rebuilds every verdict from the round sheets with its own gravity engine and
replays each filed sequence past a pristine copy of the sealed judge.
"""

from __future__ import annotations

import json
import subprocess
from functools import cache
from pathlib import Path

CARD = Path("/output/c4-card.json")
SHEETS = Path("/app/puzzles")
JUDGE = Path("/opt/tbench/judge.jar")
JUDGE_LIVE = Path("/app/bin/judge.jar")
SCHEMA = "c4-zugzwang-v1"
ROWS, COLS = 6, 7
EMPTY, YELLOW, RED = 0, 1, 2
BUDGET = 5
PAD_BAIT = 7
VERDICTS = ("win", "trap", "draw")


def idx(r: int, c: int) -> int:
    return r * COLS + c


def height(board: tuple[int, ...], c: int) -> int:
    h = 0
    while h < ROWS and board[idx(h, c)] != EMPTY:
        h += 1
    return h


def legal_cols(board: tuple[int, ...]) -> list[int]:
    return [c for c in range(COLS) if height(board, c) < ROWS]


def drop(board: tuple[int, ...], c: int, who: int) -> tuple[int, ...]:
    h = height(board, c)
    if h >= ROWS:
        raise ValueError(f"full {c}")
    cells = list(board)
    cells[idx(h, c)] = who
    return tuple(cells)


def winner(board: tuple[int, ...]) -> int:
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


@cache
def can_force(board: tuple[int, ...], stones: int) -> bool:
    if winner(board) == YELLOW:
        return True
    if winner(board) == RED or stones <= 0:
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
        if all(can_force(drop(after, rc, RED), stones - 1) for rc in rcols):
            return True
    return False


@cache
def can_coop(board: tuple[int, ...], stones: int) -> bool:
    if winner(board) == YELLOW:
        return True
    if winner(board) == RED or stones <= 0:
        return False
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW or can_coop(after, stones - 1):
            return True
    return False


def verdict(board: tuple[int, ...]) -> str:
    can_force.cache_clear()
    can_coop.cache_clear()
    if can_force(board, BUDGET):
        return "win"
    if can_coop(board, BUDGET):
        return "trap"
    return "draw"


def immediate_threats(board: tuple[int, ...]) -> list[int]:
    out = []
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            continue
        if can_coop(after, 1):
            out.append(c)
    return out


def losing_first_drops(board: tuple[int, ...]) -> list[tuple[int, int]]:
    out = []
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            continue
        for rc in legal_cols(after):
            if winner(drop(after, rc, RED)) == RED:
                out.append((c, rc))
                break
    return out


def graded_refutation_cols(board: tuple[int, ...], status: str) -> set[int]:
    if status == "trap":
        return set(immediate_threats(board))
    if status == "draw":
        cols = {c for c, _ in losing_first_drops(board)}
        for c in immediate_threats(board):
            cols.add(c)
        return cols
    return set()


def refute_ok(board: tuple[int, ...], col: int, reply: int, status: str) -> bool:
    if col not in legal_cols(board):
        return False
    after = drop(board, col, YELLOW)
    if winner(after) == YELLOW:
        return False
    if reply not in legal_cols(after):
        return False
    held = drop(after, reply, RED)
    if status == "trap":
        return not can_coop(held, 1)
    # draw: either kills Red's immediate win path used as losing-drop answer,
    # or kills a one-ply Yellow follow-up.
    if winner(held) == RED:
        return True
    return not can_coop(held, 1)


def forcing_first_cols(board: tuple[int, ...]) -> set[int]:
    out: set[int] = set()
    for c in legal_cols(board):
        after = drop(board, c, YELLOW)
        if winner(after) == YELLOW:
            out.add(c)
            continue
        rcols = legal_cols(after)
        if not rcols:
            if can_force(after, BUDGET - 1):
                out.add(c)
        elif all(can_force(drop(after, rc, RED), BUDGET - 1) for rc in rcols):
            out.add(c)
    return out


def read_sheet(path: Path):
    board_id = ""
    rows: list[str] = []
    started = False
    for raw in path.read_text().splitlines():
        text = raw.strip()
        if not text:
            continue
        if started and len(text) == COLS and len(rows) < ROWS:
            rows.append(text)
        elif text.startswith("board_id:"):
            board_id = text.split(":", 1)[1].strip()
        elif text.startswith("board:"):
            started = True
    assert len(rows) == ROWS, f"{path} grid is not {ROWS} rows"
    cells = [EMPTY] * (ROWS * COLS)
    for offset, row in enumerate(rows):
        rank = ROWS - 1 - offset
        for index, disc in enumerate(row):
            cells[idx(rank, index)] = {".": EMPTY, "Y": YELLOW, "R": RED}[disc]
    return board_id, tuple(cells)


_SHEETS: dict[str, tuple] = {}


def sheets() -> dict[str, tuple]:
    if not _SHEETS:
        for path in sorted(SHEETS.glob("board_*.txt")):
            board_id, cells = read_sheet(path)
            _SHEETS[board_id] = (cells, path)
    return _SHEETS


def card_rounds() -> dict[str, dict]:
    assert CARD.is_file(), f"{CARD} was never filed"
    body = json.loads(CARD.read_text())
    assert isinstance(body, dict), "card must be a JSON object"
    assert body.get("schema_tag") == SCHEMA, "schema_tag mismatch"
    rounds = body.get("rounds")
    assert isinstance(rounds, list), "card needs a rounds list"
    out: dict[str, dict] = {}
    for row in rounds:
        assert isinstance(row, dict), "each round must be an object"
        board_id = row.get("board_id")
        assert isinstance(board_id, str), "each round needs a board_id"
        assert board_id not in out, f"round {board_id} filed twice"
        out[board_id] = row
    return out


def judge_line(path: Path, line: list[str]) -> dict:
    seen = subprocess.run(
        [
            "java",
            "-jar",
            str(JUDGE),
            "validate",
            "--board",
            str(path),
            "--line",
            ";".join(line),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert seen.returncode == 0, f"judge refused the line: {seen.stdout}{seen.stderr}"
    return json.loads(seen.stdout)


def parse_step(step: str) -> tuple[str, int]:
    assert isinstance(step, str), "a sequence step must be a string"
    parts = step.strip().split()
    assert len(parts) == 2, f"step {step!r} needs colour and column"
    head, col_s = parts
    assert head in ("yellow", "red"), f"step {step!r} needs a colour word"
    return head, int(col_s)


def forcing_ok(board: tuple[int, ...], sequence: list[str]) -> bool:
    if not sequence:
        return False
    who = YELLOW
    stones = BUDGET
    cur = board
    for step in sequence:
        colour, col = parse_step(step)
        expect = "yellow" if who == YELLOW else "red"
        if colour != expect:
            return False
        if col not in legal_cols(cur):
            return False
        if who == YELLOW:
            if stones <= 0:
                return False
            after = drop(cur, col, YELLOW)
            if winner(after) != YELLOW:
                replies = legal_cols(after)
                if replies:
                    if not all(
                        can_force(drop(after, reply, RED), stones - 1)
                        for reply in replies
                    ):
                        return False
                elif not can_force(after, stones - 1):
                    return False
            cur = after
            stones -= 1
            if winner(cur) == YELLOW:
                return True
        else:
            cur = drop(cur, col, RED)
            if winner(cur) == YELLOW:
                return True
        who = RED if who == YELLOW else YELLOW
    return winner(cur) == YELLOW


def friendly_ok(board: tuple[int, ...], sequence: list[str]) -> bool:
    if not sequence or len(sequence) > BUDGET:
        return False
    cur = board
    for step in sequence:
        colour, col = parse_step(step)
        if colour != "yellow":
            return False
        if col not in legal_cols(cur):
            return False
        cur = drop(cur, col, YELLOW)
        if winner(cur) == YELLOW:
            return True
    return False


def refutations_ok(board: tuple[int, ...], rows: list, status: str) -> bool:
    wanted = graded_refutation_cols(board, status)
    if not wanted:
        # draw with no graded losing drops still needs empty-or-valid extras only
        if status == "draw":
            return isinstance(rows, list)
        return False
    filed: dict[int, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            return False
        col, reply = row.get("column"), row.get("reply")
        if not isinstance(col, int) or not isinstance(reply, int):
            return False
        if col in filed:
            return False
        filed[col] = reply
    if not wanted.issubset(set(filed)):
        return False
    for col, reply in filed.items():
        if not refute_ok(board, col, reply, status):
            return False
    return True


def threats_rows_ok(board: tuple[int, ...], threats: list, status: str) -> bool:
    if status == "win":
        return threats == []
    if not isinstance(threats, list):
        return False
    # Every filed threat must be a gravity landing; required threat cols ⊆ filed.
    needed = set(immediate_threats(board)) if status == "trap" else set()
    filed_cols: set[int] = set()
    for row in threats:
        if not isinstance(row, dict):
            return False
        col, r = row.get("column"), row.get("row")
        if not isinstance(col, int) or not isinstance(r, int):
            return False
        if col not in legal_cols(board):
            return False
        if height(board, col) != r:
            return False
        filed_cols.add(col)
    if status == "trap":
        return needed.issubset(filed_cols)
    return True


def round_ok(board_id: str, row: dict) -> bool:
    board, path = sheets()[board_id]
    want = verdict(board)
    if row.get("status") != want:
        return False
    if bool(row.get("coop_win")) != (want != "draw"):
        return False
    sequence = row.get("sequence")
    if not isinstance(sequence, list):
        return False
    refutations = row.get("refutations")
    if not isinstance(refutations, list):
        return False
    threats = row.get("threats")
    if not isinstance(threats, list):
        return False
    best = row.get("best_column")
    win_in = row.get("win_in")
    if not isinstance(best, int) or not isinstance(win_in, int):
        return False
    if not threats_rows_ok(board, threats, want):
        return False
    if want == "draw":
        return (
            sequence == []
            and best == -1
            and win_in == 0
            and refutations_ok(board, refutations, "draw")
        )
    if want == "win":
        if refutations or threats:
            return False
        if best not in forcing_first_cols(board):
            return False
        steps = [str(s) for s in sequence]
        if not forcing_ok(board, steps):
            return False
        seen = judge_line(path, steps)
        return (
            seen["all_legal"]
            and seen["connected"]
            and seen["yellow_drops"] == win_in
            and seen["yellow_drops"] <= BUDGET
            and sequence
            and sequence[0] == f"yellow {best}"
        )
    # trap
    steps = [str(s) for s in sequence]
    if not friendly_ok(board, steps):
        return False
    if not refutations_ok(board, refutations, "trap"):
        return False
    seen = judge_line(path, steps)
    return (
        seen["all_legal"]
        and seen["connected"]
        and seen["yellow_drops"] == win_in
        and seen["yellow_drops"] <= BUDGET
        and sequence
        and sequence[0] == f"yellow {best}"
    )


def test_a1_onyx_card_reads_as_a_tournament_card():
    """Twelve rounds, house verdict words, and empty rows only where allowed."""
    rounds = card_rounds()
    assert set(rounds) == set(sheets()), (
        f"card covers {sorted(rounds)}; booklet has {sorted(sheets())}"
    )
    ids = [r["board_id"] for r in json.loads(CARD.read_text())["rounds"]]
    assert ids == sorted(ids), "rounds must be ordered by board_id"
    for board_id, row in rounds.items():
        status = row.get("status")
        assert status in VERDICTS, f"round {board_id} status {status!r}"
        assert isinstance(row.get("sequence"), list)
        assert isinstance(row.get("refutations"), list)
        assert isinstance(row.get("threats"), list)
        assert isinstance(row.get("coop_win"), bool)
        assert isinstance(row.get("best_column"), int)
        assert isinstance(row.get("win_in"), int)
        if status == "draw":
            assert row["sequence"] == [], f"draw round {board_id} carries a sequence"
            assert row["best_column"] == -1, f"draw round {board_id} best_column"
            assert row["win_in"] == 0, f"draw round {board_id} win_in"
        else:
            assert row["sequence"], f"{status} round {board_id} carries no sequence"
            assert row["best_column"] >= 0, f"{status} round {board_id} best_column"
            assert row["win_in"] >= 1, f"{status} round {board_id} win_in"
        if status == "win":
            assert row["refutations"] == [], f"win round {board_id} carries refutations"
            assert row["threats"] == [], f"win round {board_id} carries threats"
    filed = {row["status"] for row in rounds.values()}
    assert filed == set(VERDICTS), f"card only uses {sorted(filed)}"


def test_c3_slate_filed_sequences_replay_past_the_sealed_judge():
    """The table replays every sequence: legal drops, connect, win_in matches."""
    assert JUDGE_LIVE.is_file(), "the sealed judge left the table"
    assert JUDGE_LIVE.read_bytes() == JUDGE.read_bytes(), "the sealed judge was altered"
    for path in SHEETS.glob("board_*.txt"):
        pinned = Path("/opt/tbench/puzzles") / path.name
        assert pinned.is_file(), f"missing pinned sheet {path.name}"
        assert path.read_bytes() == pinned.read_bytes(), f"sheet {path.name} was altered"
    rounds = card_rounds()
    carried = [
        (board_id, row)
        for board_id, row in sorted(rounds.items())
        if isinstance(row.get("sequence"), list) and row["sequence"]
    ]
    assert len(carried) >= 8, f"only {len(carried)} rounds carry a sequence"
    ok = 0
    for board_id, row in carried:
        _, path = sheets()[board_id]
        steps = [str(s) for s in row["sequence"]]
        try:
            seen = judge_line(path, steps)
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
        if (
            seen["all_legal"]
            and seen["connected"]
            and seen["yellow_drops"] == row.get("win_in")
            and seen["yellow_drops"] <= BUDGET
        ):
            ok += 1
    assert ok >= len(carried) - 1, f"judge accepted {ok}/{len(carried)} filed sequences"


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Verdict words must survive an independent replay of the booklet."""
    rounds = card_rounds()
    ok = 0
    for board_id, (board, _) in sorted(sheets().items()):
        row = rounds.get(board_id, {})
        want = verdict(board)
        if row.get("status") == want and bool(row.get("coop_win")) == (want != "draw"):
            ok += 1
    assert ok >= 11, f"verdicts agree on {ok}/12 rounds"


def test_g2_flint_forcing_sequences_really_force():
    """A win sequence has to hold up against every Red reply, not a soft one."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (board, _) in sorted(sheets().items())
        if verdict(board) == "win"
    ]
    ok = 0
    for board_id in wanted:
        board, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "win":
            continue
        sequence = row.get("sequence")
        best = row.get("best_column")
        if not isinstance(sequence, list) or not isinstance(best, int):
            continue
        try:
            if best in forcing_first_cols(board) and forcing_ok(
                board, [str(s) for s in sequence]
            ):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} win sequences force the connect"


def test_j4_amber_friendly_sequences_reach_four():
    """Trap sequences are Yellow alone inside five drops with Red sitting still."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (board, _) in sorted(sheets().items())
        if verdict(board) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        board, path = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "trap":
            continue
        sequence = row.get("sequence")
        if not isinstance(sequence, list):
            continue
        try:
            if friendly_ok(board, [str(s) for s in sequence]):
                seen = judge_line(path, [str(s) for s in sequence])
                if seen["connected"] and seen["yellow_drops"] == row.get("win_in"):
                    ok += 1
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} trap sequences reach four"


def test_k7_topaz_refutations_cover_every_graded_drop():
    """Trap and draw rounds need required ⊆ submitted refutation coverage."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (board, _) in sorted(sheets().items())
        if verdict(board) in ("trap", "draw")
    ]
    ok = 0
    for board_id in wanted:
        board, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        status = row.get("status")
        if status not in ("trap", "draw"):
            continue
        refs = row.get("refutations")
        threats = row.get("threats")
        if not isinstance(refs, list) or not isinstance(threats, list):
            continue
        try:
            if refutations_ok(board, refs, status) and threats_rows_ok(
                board, threats, status
            ):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} rounds cover graded drops"


def test_m2_coral_draws_are_not_seven_drop_wins():
    """Draw rounds stay draw even when a longer cooperative hunt reaches four."""
    rounds = card_rounds()
    draws = [
        board_id
        for board_id, (board, _) in sorted(sheets().items())
        if verdict(board) == "draw"
    ]
    assert draws, "booklet needs at least one draw"
    bait_hits = 0
    for board_id in draws:
        board, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        assert row.get("status") == "draw", f"round {board_id} stamped {row.get('status')}"
        assert row.get("coop_win") is False
        assert row.get("sequence") == []
        if can_coop(board, PAD_BAIT):
            bait_hits += 1
    # At least the kiosk-bait class exists somewhere in the booklet OR draws
    # carry graded losing-drop refs (parity/zugzwang without long coop).
    ref_ok = 0
    for board_id in draws:
        board, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if refutations_ok(board, row.get("refutations", []), "draw"):
            ref_ok += 1
    assert ref_ok >= len(draws) - 1, f"draw refutations ok on {ref_ok}/{len(draws)}"
    assert bait_hits >= 0  # bait optional; presence is environment texture


def test_n8_garnet_win_in_is_not_padded_past_the_connect():
    """win_in equals Yellow drops the judge counts through the connecting drop."""
    rounds = card_rounds()
    ok = 0
    checked = 0
    for board_id, row in sorted(rounds.items()):
        sequence = row.get("sequence")
        if not isinstance(sequence, list) or not sequence:
            continue
        checked += 1
        _, path = sheets()[board_id]
        try:
            seen = judge_line(path, [str(s) for s in sequence])
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
        if (
            seen["connected"]
            and seen["yellow_drops"] == row.get("win_in")
            and seen["yellow_drops"] == sum(
                1 for s in sequence if str(s).startswith("yellow ")
            )
        ):
            ok += 1
    assert checked >= 8
    assert ok >= checked - 1, f"win_in matched on {ok}/{checked}"


def test_p5_quartz_whole_booklet_stands_up():
    """Every round row must satisfy the house play contract."""
    rounds = card_rounds()
    ok = 0
    for board_id in sorted(sheets()):
        row = rounds.get(board_id)
        if row is None:
            continue
        try:
            if round_ok(board_id, row):
                ok += 1
        except (AssertionError, ValueError, json.JSONDecodeError, TypeError):
            continue
    assert ok == 12, f"whole booklet stands on {ok}/12 rounds"


def test_r6_mica_emit_twice_stays_byte_identical_on_a_finished_card():
    """Re-emitting a finished card must not rewrite its bytes."""
    assert CARD.is_file()
    before = CARD.read_bytes()
    seen = subprocess.run(
        ["/app/kiosk/emit_card.sh", str(CARD)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert seen.returncode == 0, seen.stderr
    mid = CARD.read_bytes()
    seen2 = subprocess.run(
        ["/app/kiosk/emit_card.sh", str(CARD)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert seen2.returncode == 0, seen2.stderr
    after = CARD.read_bytes()
    assert before == mid == after, "emit rewrote the finished card"
