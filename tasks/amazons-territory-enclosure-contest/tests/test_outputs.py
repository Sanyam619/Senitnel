"""Verifier for the Amazons territory enclosure booklet.

Rebuilds every verdict from the round sheets with its own queen-walk engine and
replays each filed sequence past a pristine copy of the sealed judge.
"""

from __future__ import annotations

import json
import subprocess
from functools import cache
from pathlib import Path

CARD = Path("/output/amazons-card.json")
SHEETS = Path("/app/puzzles")
JUDGE = Path("/opt/tbench/judge.jar")
JUDGE_LIVE = Path("/app/bin/judge.jar")
SCHEMA = "amazons-territory-v1"
N = 5
FILES = "abcde"
EMPTY, WHITE, BLACK, ARROW = 0, 1, 2, 3
DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
FLOOR = 2
BUDGET = 3
VERDICTS = ("win", "trap", "fort")


def name(i: int) -> str:
    return f"{FILES[i % N]}{i // N + 1}"


def spot(s: str) -> int:
    if len(s) != 2 or s[0] not in FILES or s[1] not in "12345":
        raise ValueError(f"bad square {s}")
    return (int(s[1]) - 1) * N + FILES.index(s[0])


def queen_rays(cells: tuple[int, ...], start: int) -> list[int]:
    out: list[int] = []
    sf, sr = start % N, start // N
    for df, dr in DIRS:
        f, r = sf + df, sr + dr
        while 0 <= f < N and 0 <= r < N:
            i = r * N + f
            if cells[i] != EMPTY:
                break
            out.append(i)
            f += df
            r += dr
    return out


def amazons(cells: tuple[int, ...], who: int) -> list[int]:
    return [i for i, v in enumerate(cells) if v == who]


def legal_turns(cells: tuple[int, ...], who: int) -> list[tuple[int, int, int]]:
    turns: list[tuple[int, int, int]] = []
    for src in amazons(cells, who):
        for dst in queen_rays(cells, src):
            mid = list(cells)
            mid[src] = EMPTY
            mid[dst] = who
            for arr in queen_rays(tuple(mid), dst):
                turns.append((src, dst, arr))
    return sorted(set(turns))


def apply_turn(
    cells: tuple[int, ...], turn: tuple[int, int, int], who: int
) -> tuple[int, ...]:
    src, dst, arr = turn
    board = list(cells)
    if board[src] != who:
        raise ValueError("no amazon")
    board[src] = EMPTY
    if board[dst] != EMPTY:
        raise ValueError("dst blocked")
    board[dst] = who
    if board[arr] != EMPTY:
        raise ValueError("arrow blocked")
    board[arr] = ARROW
    return tuple(board)


def reachable(cells: tuple[int, ...], who: int) -> set[int]:
    frontier = list(amazons(cells, who))
    seen = set(frontier)
    reached: set[int] = set()
    while frontier:
        cur = frontier.pop()
        for nxt in queen_rays(cells, cur):
            if nxt not in seen:
                seen.add(nxt)
                reached.add(nxt)
                frontier.append(nxt)
    return reached


def territory(cells: tuple[int, ...]) -> tuple[int, int, int]:
    w = reachable(cells, WHITE)
    b = reachable(cells, BLACK)
    we = len(w - b)
    be = len(b - w)
    return we, be, we - be


def enclosed(cells: tuple[int, ...]) -> bool:
    return territory(cells)[2] >= FLOOR


def fmt_move(turn: tuple[int, int, int]) -> str:
    a, b, c = turn
    return f"{name(a)}-{name(b)}/{name(c)}"


def parse_move(s: str) -> tuple[int, int, int]:
    left, arr = s.split("/")
    src, dst = left.split("-")
    return spot(src), spot(dst), spot(arr)


@cache
def can_force(cells: tuple[int, ...], stones: int) -> bool:
    if enclosed(cells):
        return True
    if stones <= 0:
        return False
    wt = legal_turns(cells, WHITE)
    if not wt:
        return enclosed(cells)
    for t in wt:
        after = apply_turn(cells, t, WHITE)
        if enclosed(after):
            return True
        if stones == 1:
            continue
        bt = legal_turns(after, BLACK)
        if not bt:
            if can_force(after, stones - 1):
                return True
            continue
        if all(can_force(apply_turn(after, r, BLACK), stones - 1) for r in bt):
            return True
    return False


@cache
def can_coop(cells: tuple[int, ...], stones: int) -> bool:
    if enclosed(cells):
        return True
    if stones <= 0:
        return False
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        if enclosed(after) or can_coop(after, stones - 1):
            return True
    return False


def verdict(cells: tuple[int, ...]) -> str:
    can_force.cache_clear()
    can_coop.cache_clear()
    if can_force(cells, BUDGET):
        return "win"
    if can_coop(cells, BUDGET):
        return "trap"
    return "fort"


def threats(cells: tuple[int, ...]) -> list[tuple[int, int, int]]:
    out = []
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        if enclosed(after):
            continue
        for t2 in legal_turns(after, WHITE):
            if enclosed(apply_turn(after, t2, WHITE)):
                out.append(t)
                break
    return out


def forcing_first_moves(cells: tuple[int, ...]) -> set[str]:
    out = set()
    for t in legal_turns(cells, WHITE):
        after = apply_turn(cells, t, WHITE)
        if enclosed(after):
            out.add(fmt_move(t))
            continue
        bt = legal_turns(after, BLACK)
        if not bt:
            if can_force(after, BUDGET - 1):
                out.add(fmt_move(t))
        elif all(can_force(apply_turn(after, r, BLACK), BUDGET - 1) for r in bt):
            out.add(fmt_move(t))
    return out


def read_sheet(path: Path):
    board_id = ""
    rows: list[str] = []
    started = False
    for raw in path.read_text().splitlines():
        text = raw.strip()
        if not text:
            continue
        if started and len(text) == N and len(rows) < N:
            rows.append(text)
        elif text.startswith("board_id:"):
            board_id = text.split(":", 1)[1].strip()
        elif text.startswith("board:"):
            started = True
    assert len(rows) == N, f"{path} grid is not {N} rows"
    cells = [EMPTY] * (N * N)
    for offset, row in enumerate(rows):
        rank = N - 1 - offset
        for index, disc in enumerate(row):
            cells[rank * N + index] = {
                ".": EMPTY,
                "W": WHITE,
                "B": BLACK,
                "X": ARROW,
            }[disc]
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


def parse_step(step: str):
    assert isinstance(step, str), "a sequence step must be a string"
    head, _, tail = step.strip().partition(" ")
    assert head in ("white", "black"), f"step {step!r} needs a colour word"
    return head, parse_move(tail.strip())


def forcing_ok(cells: tuple[int, ...], sequence: list[str]) -> bool:
    """Every White turn in the line must keep the floor forced with turns left."""
    if not sequence:
        return False
    who = WHITE
    stones = BUDGET
    cur = cells
    for step in sequence:
        colour, turn = parse_step(step)
        expect = "white" if who == WHITE else "black"
        if colour != expect:
            return False
        if turn not in legal_turns(cur, who):
            return False
        if who == WHITE:
            if stones <= 0:
                return False
            after = apply_turn(cur, turn, WHITE)
            if not enclosed(after):
                replies = legal_turns(after, BLACK)
                if replies:
                    if not all(
                        can_force(apply_turn(after, reply, BLACK), stones - 1)
                        for reply in replies
                    ):
                        return False
                elif not can_force(after, stones - 1):
                    return False
            cur = after
            stones -= 1
            if enclosed(cur):
                return True
        else:
            cur = apply_turn(cur, turn, BLACK)
            if enclosed(cur):
                return True
        who = BLACK if who == WHITE else WHITE
    return enclosed(cur)


def friendly_ok(cells: tuple[int, ...], sequence: list[str]) -> bool:
    if not sequence or len(sequence) > BUDGET:
        return False
    cur = cells
    for step in sequence:
        colour, turn = parse_step(step)
        if colour != "white":
            return False
        if turn not in legal_turns(cur, WHITE):
            return False
        cur = apply_turn(cur, turn, WHITE)
        if enclosed(cur):
            return True
    return False


def refutations_ok(cells: tuple[int, ...], rows: list) -> bool:
    wanted = {fmt_move(t) for t in threats(cells)}
    if not wanted:
        return False
    filed: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            return False
        move, reply = row.get("move"), row.get("reply")
        if not isinstance(move, str) or not isinstance(reply, str):
            return False
        if move in filed:
            return False
        filed[move] = reply
    if not wanted.issubset(set(filed)):
        return False
    for move, reply in filed.items():
        try:
            threat = parse_move(move)
            ans = parse_move(reply)
        except ValueError:
            return False
        if threat not in legal_turns(cells, WHITE):
            return False
        after = apply_turn(cells, threat, WHITE)
        if enclosed(after):
            return False
        if ans not in legal_turns(after, BLACK):
            return False
        held = apply_turn(after, ans, BLACK)
        if any(enclosed(apply_turn(held, t2, WHITE)) for t2 in legal_turns(held, WHITE)):
            return False
    return True


def round_ok(board_id: str, row: dict) -> bool:
    cells, path = sheets()[board_id]
    want = verdict(cells)
    if row.get("status") != want:
        return False
    if bool(row.get("coop_enclose")) != (want != "fort"):
        return False
    sequence = row.get("sequence")
    if not isinstance(sequence, list):
        return False
    refutations = row.get("refutations")
    if not isinstance(refutations, list):
        return False
    best = row.get("best_move")
    delta = row.get("territory_delta")
    if want == "fort":
        return (
            sequence == []
            and refutations == []
            and best == ""
            and delta == 0
        )
    if not isinstance(best, str) or not isinstance(delta, int):
        return False
    if want == "win":
        if refutations:
            return False
        if best not in forcing_first_moves(cells):
            return False
        if not forcing_ok(cells, [str(s) for s in sequence]):
            return False
        seen = judge_line(path, [str(s) for s in sequence])
        return (
            seen["all_legal"]
            and seen["enclosed"]
            and seen["territory_delta"] == delta
            and seen["white_turns"] <= BUDGET
            and sequence
            and sequence[0] == f"white {best}"
        )
    # trap
    if not friendly_ok(cells, [str(s) for s in sequence]):
        return False
    if not refutations_ok(cells, refutations):
        return False
    seen = judge_line(path, [str(s) for s in sequence])
    return (
        seen["all_legal"]
        and seen["enclosed"]
        and seen["territory_delta"] == delta
        and seen["white_turns"] <= BUDGET
        and sequence
        and sequence[0] == f"white {best}"
    )


def test_a1_onyx_card_reads_as_a_tournament_card():
    """Eleven rounds, house verdict words, and empty rows only where allowed."""
    rounds = card_rounds()
    assert set(rounds) == set(sheets()), (
        f"card covers {sorted(rounds)}; booklet has {sorted(sheets())}"
    )
    ids = [r["board_id"] for r in json.loads(CARD.read_text())["rounds"]]
    assert ids == sorted(ids), "rounds must be ordered by board_id"
    for board_id, row in rounds.items():
        status = row.get("status")
        assert status in VERDICTS, f"round {board_id} status {status!r}"
        assert isinstance(row.get("sequence"), list), (
            f"round {board_id} sequence must be a list"
        )
        assert isinstance(row.get("refutations"), list), (
            f"round {board_id} refutations must be a list"
        )
        assert isinstance(row.get("coop_enclose"), bool), (
            f"round {board_id} coop_enclose must be bool"
        )
        if status == "fort":
            assert row["sequence"] == [], f"fort round {board_id} carries a sequence"
            assert row["best_move"] == "", f"fort round {board_id} carries a best_move"
        else:
            assert row["sequence"], f"{status} round {board_id} carries no sequence"
            assert row["best_move"], f"{status} round {board_id} carries no best_move"
        if status != "trap":
            assert row["refutations"] == [], (
                f"{status} round {board_id} carries refutations"
            )
    filed = {row["status"] for row in rounds.values()}
    assert filed == set(VERDICTS), f"card only uses {sorted(filed)}"


def test_c3_slate_filed_sequences_replay_past_the_sealed_judge():
    """The table replays every sequence: legal turns, floor met, delta matches."""
    assert JUDGE_LIVE.is_file(), "the sealed judge left the table"
    assert JUDGE_LIVE.read_bytes() == JUDGE.read_bytes(), "the sealed judge was altered"
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
            and seen["enclosed"]
            and seen["territory_delta"] == row.get("territory_delta")
            and seen["white_turns"] <= BUDGET
        ):
            ok += 1
    assert ok >= len(carried) - 1, f"judge accepted {ok}/{len(carried)} filed sequences"


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Verdict words must survive an independent replay of the booklet."""
    rounds = card_rounds()
    ok = 0
    for board_id, (cells, _) in sorted(sheets().items()):
        row = rounds.get(board_id, {})
        if row.get("status") == verdict(cells) and bool(row.get("coop_enclose")) == (
            verdict(cells) != "fort"
        ):
            ok += 1
    assert ok >= 10, f"verdicts agree on {ok}/11 rounds"


def test_g2_flint_forcing_sequences_really_force():
    """A win sequence has to hold up against every Black reply, not a soft one."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, _) in sorted(sheets().items())
        if verdict(cells) == "win"
    ]
    ok = 0
    for board_id in wanted:
        cells, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "win":
            continue
        sequence = row.get("sequence")
        best = row.get("best_move")
        if not isinstance(sequence, list) or not isinstance(best, str):
            continue
        try:
            if best in forcing_first_moves(cells) and forcing_ok(
                cells, [str(s) for s in sequence]
            ):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} win sequences force the floor"


def test_j4_amber_friendly_sequences_reach_the_floor():
    """Trap sequences are White alone inside three turns with Black sitting still."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, _) in sorted(sheets().items())
        if verdict(cells) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        cells, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "trap":
            continue
        sequence = row.get("sequence")
        if not isinstance(sequence, list):
            continue
        try:
            if friendly_ok(cells, [str(s) for s in sequence]):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} friendly sequences reach the floor"


def test_k7_topaz_refutations_cover_every_threat():
    """Black must answer each region-splitting threat, and only real answers count."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, _) in sorted(sheets().items())
        if verdict(cells) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        cells, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        rows = row.get("refutations")
        if row.get("status") != "trap" or not isinstance(rows, list):
            continue
        try:
            if refutations_ok(cells, rows):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} trap rounds fully refuted"


def test_m8_jade_forts_are_not_the_kiosk_cheer():
    """The kiosk stamps a win wherever a fourth turn reaches; the table does not."""
    rounds = card_rounds()
    forts = [
        board_id
        for board_id, (cells, _) in sorted(sheets().items())
        if verdict(cells) == "fort"
    ]
    assert forts, "booklet lost its fort rounds"
    held = sum(1 for board_id in forts if rounds.get(board_id, {}).get("status") == "fort")
    assert held >= len(forts) - 1, f"{held}/{len(forts)} fort rounds filed as forts"
    optimistic = sum(1 for row in rounds.values() if row.get("status") == "win")
    assert optimistic < len(rounds), "every round filed as a win"
    # fourth-turn coop succeeds on forts — proves the kiosk bait is live
    for board_id in forts:
        cells, _ = sheets()[board_id]
        assert can_coop(cells, 4), f"fort {board_id} is not fourth-turn coop bait"


def test_n2_coral_territory_delta_is_not_padded():
    """Filed deltas must match the sealed judge after the sequence, not a padded boast."""
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
        if seen.get("territory_delta") == row.get("territory_delta") and seen.get(
            "enclosed"
        ):
            ok += 1
    assert checked >= 8
    assert ok >= checked - 1, f"delta matched on {ok}/{checked} sequenced rounds"


def test_p5_quartz_whole_booklet_stands_up():
    """Near-exact booklet: verdict, play, refutations, and deltas together."""
    rounds = card_rounds()
    ok = 0
    for board_id in sorted(sheets()):
        row = rounds.get(board_id)
        if not isinstance(row, dict):
            continue
        try:
            if round_ok(board_id, row):
                ok += 1
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
    assert ok >= 10, f"{ok}/11 rounds stand up end to end"


def test_r6_mica_emit_twice_stays_byte_identical_on_a_finished_card(tmp_path):
    """A finished card must come out the same bytes when the desk emits twice."""
    assert CARD.is_file() and CARD.stat().st_size > 0
    body = json.loads(CARD.read_text())
    staged = tmp_path / "amazons-card.json"
    staged.write_bytes(CARD.read_bytes())
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
    assert json.loads(first) == body
