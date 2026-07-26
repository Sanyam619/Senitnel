"""Verifier for the Abalone marble-push booklet.

Rebuilds every verdict from the round sheets with its own sumito rules and
replays each filed sequence past a pristine copy of the sealed judge.
"""

from __future__ import annotations

import json
import subprocess
from functools import cache
from pathlib import Path

CARD = Path("/app/answers.json")
SHEETS = Path("/app/puzzles")
JUDGE = Path("/opt/tbench/judge.jar")
JUDGE_LIVE = Path("/app/bin/judge.jar")
DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))
R = 2
EMPTY, BLACK, WHITE = 0, 1, 2
FLOOR = 1
BUDGET = 3
VERDICTS = ("win", "trap", "fort")


def _cells() -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for q in range(-R, R + 1):
        for r in range(-R, R + 1):
            if max(abs(q), abs(r), abs(-q - r)) <= R:
                out.append((q, r))
    return out


CELLS = _cells()
IDX = {c: i for i, c in enumerate(CELLS)}
N = len(CELLS)


def name(i: int) -> str:
    q, r = CELLS[i]
    return f"{chr(ord('a') + q + R)}{r + R + 1}"


def spot(s: str) -> int:
    q = ord(s[0]) - ord("a") - R
    r = int(s[1]) - R - 1
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
    board = [EMPTY] * N
    for vi, glyphs in enumerate(rows):
        r = R - vi
        qs = sorted(
            q for q in range(-R, R + 1) if max(abs(q), abs(r), abs(q + r)) <= R
        )
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
        return f"{body}>{name(land)}" if land is not None else f"{body}>off"
    _, ordered, side = mv
    body = "".join(name(c) for c in ordered)
    land = step(ordered[0], side)
    assert land is not None
    return f"{body}>{name(land)}"


def parse_move(cells: tuple[int, ...], s: str, who: int) -> tuple:
    for mv in legal_moves(cells, who):
        if fmt_move(mv) == s:
            return mv
    raise ValueError(f"illegal move {s}")


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
            raise ValueError("suicide")
        if cells[land] == EMPTY:
            for c in chain:
                board[c] = EMPTY
            for c in chain:
                board[step(c, d)] = who  # type: ignore[index]
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
            board[step(c, d)] = who  # type: ignore[index]
        return tuple(board), ejected
    _, ordered, side = mv
    lands = [step(c, side) for c in ordered]
    for c in ordered:
        board[c] = EMPTY
    for L in lands:
        board[L] = who  # type: ignore[index]
    return tuple(board), 0


def goal_met(ejected: int) -> bool:
    return ejected >= FLOOR


@cache
def can_force(cells: tuple[int, ...], stones: int, ejected: int) -> bool:
    if goal_met(ejected):
        return True
    if stones <= 0:
        return False
    for mv in legal_moves(cells, BLACK):
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


def read_sheet(path: Path):
    text = path.read_text()
    board_id = ""
    for line in text.splitlines():
        if line.startswith("board_id:"):
            board_id = line.split(":", 1)[1].strip()
            break
    return board_id, parse_board(text)


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


def parse_step(cells, step_s: str):
    head, _, tail = step_s.strip().partition(" ")
    assert head in ("black", "white"), f"step {step_s!r} needs a colour word"
    who = BLACK if head == "black" else WHITE
    return head, parse_move(cells, tail.strip(), who), who


def forcing_ok(cells: tuple[int, ...], sequence: list[str]) -> bool:
    if not sequence:
        return False
    who = BLACK
    stones = BUDGET
    cur = cells
    ejected = 0
    for step_s in sequence:
        colour, turn, _who = parse_step(cur, step_s)
        expect = "black" if who == BLACK else "white"
        if colour != expect:
            return False
        if turn not in legal_moves(cur, who):
            return False
        if who == BLACK:
            if stones <= 0:
                return False
            after, ej = apply_move(cur, turn, BLACK)
            ne = ejected + ej
            if not goal_met(ne):
                replies = legal_moves(after, WHITE)
                if replies:
                    if not all(
                        can_force(apply_move(after, reply, WHITE)[0], stones - 1, ne)
                        for reply in replies
                    ):
                        return False
                elif not can_force(after, stones - 1, ne):
                    return False
            cur = after
            ejected = ne
            stones -= 1
            if goal_met(ejected):
                return True
        else:
            cur, _ = apply_move(cur, turn, WHITE)
            if goal_met(ejected):
                return True
        who = WHITE if who == BLACK else BLACK
    return goal_met(ejected)


def friendly_ok(cells: tuple[int, ...], sequence: list[str]) -> bool:
    if not sequence or len(sequence) > BUDGET:
        return False
    cur = cells
    ejected = 0
    for step_s in sequence:
        colour, turn, who = parse_step(cur, step_s)
        if colour != "black" or who != BLACK:
            return False
        if turn not in legal_moves(cur, BLACK):
            return False
        cur, ej = apply_move(cur, turn, BLACK)
        ejected += ej
        if goal_met(ejected):
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
            threat = parse_move(cells, move, BLACK)
            ans = parse_move(apply_move(cells, threat, BLACK)[0], reply, WHITE)
        except ValueError:
            return False
        after, ej = apply_move(cells, threat, BLACK)
        if goal_met(ej):
            return False
        if ans not in legal_moves(after, WHITE):
            return False
        held, _ = apply_move(after, ans, WHITE)
        if any(
            goal_met(ej + apply_move(held, t2, BLACK)[1])
            for t2 in legal_moves(held, BLACK)
        ):
            return False
    return True


def round_ok(board_id: str, row: dict) -> bool:
    cells, path = sheets()[board_id]
    want = verdict(cells)
    if row.get("status") != want:
        return False
    if bool(row.get("coop_eject")) != (want != "fort"):
        return False
    sequence = row.get("sequence")
    if not isinstance(sequence, list):
        return False
    refutations = row.get("refutations")
    if not isinstance(refutations, list):
        return False
    key = row.get("key_push")
    ejected = row.get("ejected")
    if want == "fort":
        return (
            sequence == []
            and refutations == []
            and key == ""
            and ejected == 0
        )
    if not isinstance(key, str) or not isinstance(ejected, int):
        return False
    if want == "win":
        if refutations:
            return False
        if key not in forcing_first_moves(cells):
            return False
        if not forcing_ok(cells, [str(s) for s in sequence]):
            return False
        seen = judge_line(path, [str(s) for s in sequence])
        return (
            seen["all_legal"]
            and seen["enclosed"]
            and seen["ejected"] == ejected
            and seen["black_turns"] <= BUDGET
            and sequence
            and sequence[0] == f"black {key}"
        )
    if not friendly_ok(cells, [str(s) for s in sequence]):
        return False
    if not refutations_ok(cells, refutations):
        return False
    seen = judge_line(path, [str(s) for s in sequence])
    return (
        seen["all_legal"]
        and seen["enclosed"]
        and seen["ejected"] == ejected
        and seen["black_turns"] <= BUDGET
        and sequence
        and sequence[0] == f"black {key}"
    )


def test_a1_onyx_card_reads_as_a_tournament_card():
    """Ten rounds, house verdict words, and empty rows only where allowed."""
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
        assert isinstance(row.get("coop_eject"), bool)
        if status == "fort":
            assert row["sequence"] == []
            assert row["key_push"] == ""
        else:
            assert row["sequence"]
            assert row["key_push"]
        if status != "trap":
            assert row["refutations"] == []
    filed = {row["status"] for row in rounds.values()}
    assert filed == set(VERDICTS), f"card only uses {sorted(filed)}"


def test_c3_slate_filed_sequences_replay_past_the_sealed_judge():
    """The table replays every sequence: legal turns, floor met, ejected matches."""
    assert JUDGE_LIVE.is_file(), "the sealed judge left the table"
    assert JUDGE_LIVE.read_bytes() == JUDGE.read_bytes(), "the sealed judge was altered"
    rounds = card_rounds()
    carried = [
        (board_id, row)
        for board_id, row in sorted(rounds.items())
        if isinstance(row.get("sequence"), list) and row["sequence"]
    ]
    assert len(carried) >= 7, f"only {len(carried)} rounds carry a sequence"
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
            and seen["ejected"] == row.get("ejected")
            and seen["black_turns"] <= BUDGET
        ):
            ok += 1
    assert ok >= len(carried) - 1, f"judge accepted {ok}/{len(carried)} filed sequences"


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Verdict words must survive an independent replay of the booklet."""
    rounds = card_rounds()
    ok = 0
    for board_id, (cells, _) in sorted(sheets().items()):
        row = rounds.get(board_id, {})
        if row.get("status") == verdict(cells) and bool(row.get("coop_eject")) == (
            verdict(cells) != "fort"
        ):
            ok += 1
    assert ok >= 9, f"verdicts agree on {ok}/10 rounds"


def test_g2_flint_forcing_sequences_really_force():
    """A win sequence has to hold up against every White reply, not a soft one."""
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
        key = row.get("key_push")
        if not isinstance(sequence, list) or not isinstance(key, str):
            continue
        try:
            if key in forcing_first_moves(cells) and forcing_ok(
                cells, [str(s) for s in sequence]
            ):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} win sequences force the floor"


def test_j4_amber_friendly_sequences_reach_the_floor():
    """Trap sequences are Black alone inside three turns with White sitting still."""
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
    """White must answer each over-push threat, and only real answers count."""
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
    for board_id in forts:
        cells, _ = sheets()[board_id]
        assert can_coop(cells, 4, 0), f"fort {board_id} is not fourth-turn coop bait"


def test_n2_coral_ejected_is_not_padded():
    """Filed ejected counts must match the sealed judge after the sequence."""
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
        if seen.get("ejected") == row.get("ejected") and seen.get("enclosed"):
            ok += 1
    assert checked >= 7
    assert ok >= checked - 1, f"ejected matched on {ok}/{checked} sequenced rounds"


def test_p5_quartz_whole_booklet_stands_up():
    """Near-exact booklet: verdict, play, refutations, and ejected together."""
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
    assert ok >= 9, f"{ok}/10 rounds stand up end to end"


def test_r6_mica_emit_twice_stays_byte_identical_on_a_finished_card(tmp_path):
    """A finished card must come out the same bytes when the desk emits twice."""
    assert CARD.is_file() and CARD.stat().st_size > 0
    staged = tmp_path / "answers.json"
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
    assert first == staged.read_bytes()
    assert first == CARD.read_bytes()
