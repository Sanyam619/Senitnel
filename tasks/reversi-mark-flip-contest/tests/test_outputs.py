"""Verifier for the Reversi marked-disc booklet.

Rebuilds every verdict from the round sheets with its own cell-walking engine and
replays each filed line past a pristine copy of the sealed judge.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

CARD = Path("/app/answers.json")
SHEETS = Path("/app/puzzles")
JUDGE = Path("/opt/tbench/judge.jar")
STONES = 3
FILE_LETTERS = "abcdefgh"
CORNERS = ("a1", "h1", "a8", "h8")
VERDICTS = ("win", "trap", "fort")

STEPS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def _rays() -> tuple[tuple[tuple[int, ...], ...], ...]:
    table = []
    for spot in range(64):
        here = []
        for df, dr in STEPS:
            walk = []
            f, r = spot % 8 + df, spot // 8 + dr
            while 0 <= f < 8 and 0 <= r < 8:
                walk.append(r * 8 + f)
                f += df
                r += dr
            here.append(tuple(walk))
        table.append(tuple(here))
    return tuple(table)


RAYS = _rays()


def name_of(spot: int) -> str:
    return f"{FILE_LETTERS[spot % 8]}{spot // 8 + 1}"


def spot_of(square: str) -> int:
    if len(square) != 2 or square[0] not in FILE_LETTERS or square[1] not in "12345678":
        raise ValueError(f"bad square {square}")
    return (ord(square[1]) - ord("1")) * 8 + FILE_LETTERS.index(square[0])


def turns(cells: tuple[int, ...], spot: int, who: int) -> tuple[int, ...]:
    """Discs that turn over when `who` drops on `spot`."""
    if cells[spot]:
        return ()
    foe = 3 - who
    got: list[int] = []
    for ray in RAYS[spot]:
        run: list[int] = []
        for idx in ray:
            here = cells[idx]
            if here == foe:
                run.append(idx)
            elif here == who:
                got.extend(run)
                break
            else:
                break
    return tuple(got)


_DROPS: dict[tuple, tuple[int, ...]] = {}


def open_drops(cells: tuple[int, ...], who: int) -> tuple[int, ...]:
    key = (cells, who)
    hit = _DROPS.get(key)
    if hit is None:
        hit = tuple(spot for spot in range(64) if turns(cells, spot, who))
        _DROPS[key] = hit
    return hit


def drop(cells: tuple[int, ...], spot: int, who: int) -> tuple[int, ...]:
    flipped = turns(cells, spot, who)
    if not flipped:
        raise ValueError(f"illegal drop {name_of(spot)}")
    board = list(cells)
    board[spot] = who
    for idx in flipped:
        board[idx] = who
    return tuple(board)


def call_of(cells: tuple[int, ...], spot: int, who: int) -> str:
    tag = f"flips:{len(turns(cells, spot, who))}"
    return tag + "+corner" if name_of(spot) in CORNERS else tag


_FORCED: dict[tuple, bool] = {}


def forced(cells: tuple[int, ...], mark: int, stones: int) -> bool:
    """Black to move: is the take unavoidable inside `stones` however White fights?"""
    if cells[mark] == 1:
        return True
    if stones <= 0:
        return False
    key = (cells, mark, stones)
    hit = _FORCED.get(key)
    if hit is not None:
        return hit
    answer = False
    mine = open_drops(cells, 1)
    if not mine:
        theirs = open_drops(cells, 2)
        answer = bool(theirs) and all(
            forced(drop(cells, reply, 2), mark, stones) for reply in theirs
        )
    else:
        for spot in mine:
            after = drop(cells, spot, 1)
            if after[mark] == 1:
                answer = True
                break
            if stones == 1:
                continue
            replies = open_drops(after, 2)
            if not replies:
                if forced(after, mark, stones - 1):
                    answer = True
                    break
                continue
            if all(
                forced(drop(after, reply, 2), mark, stones - 1) for reply in replies
            ):
                answer = True
                break
    _FORCED[key] = answer
    return answer


_FRIENDLY: dict[tuple, bool] = {}


def friendly(cells: tuple[int, ...], mark: int, stones: int) -> bool:
    """White passes every turn: does Black reach the mark inside `stones`?"""
    if cells[mark] == 1:
        return True
    if stones <= 0:
        return False
    key = (cells, mark, stones)
    hit = _FRIENDLY.get(key)
    if hit is not None:
        return hit
    answer = False
    for spot in open_drops(cells, 1):
        after = drop(cells, spot, 1)
        if after[mark] == 1 or friendly(after, mark, stones - 1):
            answer = True
            break
    _FRIENDLY[key] = answer
    return answer


def finishers(cells: tuple[int, ...], mark: int) -> tuple[int, ...]:
    return tuple(
        spot for spot in open_drops(cells, 1) if drop(cells, spot, 1)[mark] == 1
    )


def threats(cells: tuple[int, ...], mark: int) -> tuple[int, ...]:
    out = []
    for spot in open_drops(cells, 1):
        after = drop(cells, spot, 1)
        if after[mark] == 1:
            continue
        if finishers(after, mark):
            out.append(spot)
    return tuple(out)


def verdict(cells: tuple[int, ...], mark: int) -> str:
    if forced(cells, mark, STONES):
        return "win"
    if friendly(cells, mark, STONES):
        return "trap"
    return "fort"


def read_sheet(path: Path):
    board_id = ""
    mark = -1
    rows: list[str] = []
    started = False
    for raw in path.read_text().splitlines():
        text = raw.strip()
        if not text:
            continue
        if started and len(text) == 8 and len(rows) < 8:
            rows.append(text)
        elif text.startswith("board_id:"):
            board_id = text.split(":", 1)[1].strip()
        elif text.startswith("mark:"):
            mark = spot_of(text.split(":", 1)[1].strip())
        elif text.startswith("board:"):
            started = True
    assert len(rows) == 8, f"{path} grid is not eight rows"
    assert mark >= 0, f"{path} has no mark"
    cells = [0] * 64
    for offset, row in enumerate(reversed(rows)):
        for index, disc in enumerate(row):
            cells[offset * 8 + index] = 1 if disc == "B" else (2 if disc == "W" else 0)
    return board_id, tuple(cells), mark


_SHEETS: dict[str, tuple] = {}


def sheets() -> dict[str, tuple]:
    if not _SHEETS:
        for path in sorted(SHEETS.glob("board_*.txt")):
            board_id, cells, mark = read_sheet(path)
            _SHEETS[board_id] = (cells, mark, path)
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


def parse_step(step: str):
    """('black', spot|None, announce|None) for one filed step."""
    assert isinstance(step, str), "a line step must be a string"
    head, _, tail = step.strip().partition(" ")
    assert head in ("black", "white"), f"step {step!r} needs a colour word"
    square, _, call = tail.strip().partition("|")
    square = square.strip()
    if square == "pass":
        return head, None, None
    return head, spot_of(square), call.strip() or None


def calls_present(line: list[str]) -> bool:
    """Every drop in a filed line has to carry the house announce."""
    for step in line:
        colour, spot, call = parse_step(step)
        del colour
        if spot is not None and not call:
            return False
    return True


def forcing_ok(cells: tuple[int, ...], mark: int, line: list[str]) -> bool:
    """Every Black drop in the line must keep the take forced with stones left."""
    who = 1
    stones = STONES
    if not calls_present(line):
        return False
    for step in line:
        colour, spot, call = parse_step(step)
        if colour != ("black" if who == 1 else "white"):
            return False
        if spot is None:
            if open_drops(cells, who):
                return False
            who = 3 - who
            continue
        if not turns(cells, spot, who):
            return False
        if call != call_of(cells, spot, who):
            return False
        if who == 1:
            if stones <= 0:
                return False
            after = drop(cells, spot, 1)
            if after[mark] != 1:
                replies = open_drops(after, 2)
                if replies:
                    if not all(
                        forced(drop(after, reply, 2), mark, stones - 1)
                        for reply in replies
                    ):
                        return False
                elif not forced(after, mark, stones - 1):
                    return False
            cells = after
            stones -= 1
            if cells[mark] == 1:
                return True
        else:
            cells = drop(cells, spot, who)
        who = 3 - who
    return cells[mark] == 1


def friendly_ok(cells: tuple[int, ...], mark: int, line: list[str]) -> bool:
    """Black-only drops, at most three, reaching the mark while White sits still."""
    if not line or len(line) > STONES or not calls_present(line):
        return False
    for step in line:
        colour, spot, call = parse_step(step)
        if colour != "black" or spot is None:
            return False
        if not turns(cells, spot, 1):
            return False
        if call != call_of(cells, spot, 1):
            return False
        cells = drop(cells, spot, 1)
        if cells[mark] == 1:
            return True
    return False


def refutations_ok(cells: tuple[int, ...], mark: int, rows: list) -> bool:
    wanted = {name_of(spot) for spot in threats(cells, mark)}
    if not wanted:
        return False
    filed: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            return False
        threat, reply = row.get("threat"), row.get("reply")
        if not isinstance(threat, str) or not isinstance(reply, str):
            return False
        if threat in filed:
            return False
        filed[threat] = reply
    if set(filed) != wanted:
        return False
    for threat, reply in filed.items():
        after = drop(cells, spot_of(threat), 1)
        replies = open_drops(after, 2)
        if reply == "pass":
            if replies or finishers(after, mark):
                return False
            continue
        try:
            spot = spot_of(reply)
        except ValueError:
            return False
        if spot not in replies:
            return False
        held = drop(after, spot, 2)
        if held[mark] == 1 or finishers(held, mark):
            return False
    return True


def round_ok(board_id: str, row: dict) -> bool:
    cells, mark, path = sheets()[board_id]
    want = verdict(cells, mark)
    if row.get("status") != want:
        return False
    line = row.get("line")
    if not isinstance(line, list):
        return False
    refutations = row.get("refutations")
    if not isinstance(refutations, list):
        return False
    if want == "fort":
        return line == [] and refutations == []
    if want == "win":
        if refutations:
            return False
        return forcing_ok(cells, mark, line) and judge_line(path, line)["all_legal"]
    return friendly_ok(cells, mark, line) and refutations_ok(cells, mark, refutations)


def test_a1_onyx_card_reads_as_a_tournament_card():
    """Eleven rounds, house verdict words, and empty rows only where allowed."""
    rounds = card_rounds()
    assert set(rounds) == set(sheets()), (
        f"card covers {sorted(rounds)}; booklet has {sorted(sheets())}"
    )
    for board_id, row in rounds.items():
        status = row.get("status")
        assert status in VERDICTS, f"round {board_id} status {status!r}"
        assert isinstance(row.get("line"), list), f"round {board_id} line must be a list"
        assert isinstance(row.get("refutations"), list), (
            f"round {board_id} refutations must be a list"
        )
        if status == "fort":
            assert row["line"] == [], f"fort round {board_id} carries a line"
        else:
            assert row["line"], f"{status} round {board_id} carries no line"
        if status != "trap":
            assert row["refutations"] == [], (
                f"{status} round {board_id} carries refutations"
            )
    filed = {row["status"] for row in rounds.values()}
    assert filed == set(VERDICTS), f"card only uses {sorted(filed)}"


def test_c3_slate_filed_lines_replay_past_the_sealed_judge():
    """The table replays every line: legal drops, house announces, mark turned."""
    live = Path("/app/bin/judge.jar")
    assert live.is_file(), "the sealed judge left the table"
    assert live.read_bytes() == JUDGE.read_bytes(), "the sealed judge was altered"
    rounds = card_rounds()
    carried = [
        (board_id, row)
        for board_id, row in sorted(rounds.items())
        if isinstance(row.get("line"), list) and row["line"]
    ]
    assert len(carried) >= 8, f"only {len(carried)} rounds carry a line"
    ok = 0
    for board_id, row in carried:
        _, _, path = sheets()[board_id]
        steps = [str(s) for s in row["line"]]
        try:
            if not calls_present(steps):
                continue
            seen = judge_line(path, steps)
        except (AssertionError, ValueError):
            continue
        if (
            seen["all_legal"]
            and seen["announce_all_ok"]
            and seen["mark_turned_black"]
            and seen["black_drops"] <= STONES
        ):
            ok += 1
    assert ok >= len(carried) - 1, f"judge accepted {ok}/{len(carried)} filed lines"


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Verdict words must survive an independent replay of the booklet."""
    rounds = card_rounds()
    ok = 0
    for board_id, (cells, mark, _) in sorted(sheets().items()):
        if rounds.get(board_id, {}).get("status") == verdict(cells, mark):
            ok += 1
    assert ok >= 10, f"verdicts agree on {ok}/11 rounds"


def test_g2_flint_forcing_lines_really_force():
    """A win line has to hold up against every White reply, not a soft one."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, mark, _) in sorted(sheets().items())
        if verdict(cells, mark) == "win"
    ]
    ok = 0
    for board_id in wanted:
        cells, mark, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "win":
            continue
        line = row.get("line")
        if not isinstance(line, list):
            continue
        try:
            if forcing_ok(cells, mark, [str(s) for s in line]):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} win lines force the take"


def test_j4_amber_friendly_lines_reach_the_mark():
    """Trap lines are Black alone inside three stones with White sitting still."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, mark, _) in sorted(sheets().items())
        if verdict(cells, mark) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        cells, mark, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "trap":
            continue
        line = row.get("line")
        if not isinstance(line, list):
            continue
        try:
            if friendly_ok(cells, mark, [str(s) for s in line]):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} friendly lines reach the mark"


def test_k7_topaz_refutations_cover_every_threat():
    """White must answer each threat on the sheet, and only the real ones."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, mark, _) in sorted(sheets().items())
        if verdict(cells, mark) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        cells, mark, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        rows = row.get("refutations")
        if row.get("status") != "trap" or not isinstance(rows, list):
            continue
        try:
            if refutations_ok(cells, mark, rows):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} trap rounds fully refuted"


def test_m8_jade_forts_are_not_the_kiosk_cheer():
    """The kiosk stamps a win wherever a fourth stone reaches; the table does not."""
    rounds = card_rounds()
    forts = [
        board_id
        for board_id, (cells, mark, _) in sorted(sheets().items())
        if verdict(cells, mark) == "fort"
    ]
    assert forts, "booklet lost its fort rounds"
    held = sum(1 for board_id in forts if rounds.get(board_id, {}).get("status") == "fort")
    assert held >= len(forts) - 1, f"{held}/{len(forts)} fort rounds filed as forts"
    optimistic = sum(1 for row in rounds.values() if row.get("status") == "win")
    assert optimistic < len(rounds), "every round filed as a win"


def test_p5_quartz_whole_booklet_stands_up():
    """Near-exact booklet: verdict, play, and refutations together."""
    rounds = card_rounds()
    ok = 0
    for board_id in sorted(sheets()):
        row = rounds.get(board_id)
        if not isinstance(row, dict):
            continue
        try:
            if round_ok(board_id, row):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= 10, f"{ok}/11 rounds stand up end to end"
