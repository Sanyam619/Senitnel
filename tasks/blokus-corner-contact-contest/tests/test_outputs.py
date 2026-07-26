"""Verifier for the Blokus corner-contact booklet.

Rebuilds every verdict from the round sheets with its own packing engine and
replays each filed sequence past a pristine copy of the sealed judge.
"""

from __future__ import annotations

import json
import subprocess
from functools import cache
from pathlib import Path

CARD = Path("/output/blokus-card.json")
SHEETS = Path("/app/puzzles")
JUDGE = Path("/opt/tbench/judge.jar")
JUDGE_LIVE = Path("/app/bin/judge.jar")
SCHEMA = "blokus-corner-v1"
N = 5
FILES = "abcde"
EMPTY, BLUE, YELLOW, BLOCK = 0, 1, 2, 3
FLOOR = 0
BUDGET = 3
VERDICTS = ("win", "trap", "fort")
EDGE = ((-1, 0), (1, 0), (0, -1), (0, 1))
CORNER = ((-1, -1), (-1, 1), (1, -1), (1, 1))

RAW = {
    "1": [(0, 0)],
    "2": [(0, 0), (1, 0)],
    "I3": [(0, 0), (1, 0), (2, 0)],
    "V3": [(0, 0), (0, 1), (1, 0)],
    "I4": [(0, 0), (1, 0), (2, 0), (3, 0)],
    "O4": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T4": [(0, 0), (1, 0), (2, 0), (1, 1)],
    "L4": [(0, 0), (0, 1), (0, 2), (1, 2)],
    "S4": [(1, 0), (2, 0), (0, 1), (1, 1)],
}


def rotations(cells: list[tuple[int, int]]) -> list[tuple[tuple[int, int], ...]]:
    out: set[tuple[tuple[int, int], ...]] = set()
    pts = cells
    for _ in range(4):
        for reflect in (False, True):
            cur = pts
            if reflect:
                cur = [(-x, y) for x, y in cur]
            minx = min(x for x, _ in cur)
            miny = min(y for _, y in cur)
            norm = tuple(sorted((x - minx, y - miny) for x, y in cur))
            out.add(norm)
        pts = [(y, -x) for x, y in pts]
    return [tuple(p) for p in sorted(out)]


ORIENTS = {pid: rotations(shape) for pid, shape in RAW.items()}
SIZE = {pid: len(shape) for pid, shape in RAW.items()}


def name(i: int) -> str:
    return f"{FILES[i % N]}{i // N + 1}"


def spot(s: str) -> int:
    if len(s) != 2 or s[0] not in FILES or s[1] not in "12345":
        raise ValueError(f"bad square {s}")
    return (int(s[1]) - 1) * N + FILES.index(s[0])


def neighbors(i: int, deltas):
    f, r = i % N, i // N
    for df, dr in deltas:
        nf, nr = f + df, r + dr
        if 0 <= nf < N and 0 <= nr < N:
            yield nr * N + nf


def squares_of(pid: str, anchor: int, oi: int) -> tuple[int, ...] | None:
    shape = ORIENTS[pid][oi]
    af, ar = anchor % N, anchor // N
    cells = []
    for dx, dy in shape:
        f, r = af + dx, ar + dy
        if not (0 <= f < N and 0 <= r < N):
            return None
        cells.append(r * N + f)
    return tuple(sorted(cells))


def fmt_placement(pid: str, cells: tuple[int, ...]) -> str:
    return f"{pid}@{','.join(name(c) for c in cells)}"


def parse_placement(s: str) -> tuple[str, tuple[int, ...]]:
    pid, rest = s.split("@", 1)
    cells = tuple(sorted(spot(x) for x in rest.split(",")))
    return pid, cells


def has_own(cells: tuple[int, ...], who: int) -> bool:
    return any(v == who for v in cells)


def legal_on(
    cells: tuple[int, ...], who: int, pid: str, place: tuple[int, ...]
) -> bool:
    if pid not in SIZE or len(place) != SIZE[pid]:
        return False
    ok_shape = False
    for oi in range(len(ORIENTS[pid])):
        for a in range(N * N):
            got = squares_of(pid, a, oi)
            if got == place:
                ok_shape = True
                break
        if ok_shape:
            break
    if not ok_shape:
        return False
    for c in place:
        if cells[c] != EMPTY:
            return False
    for c in place:
        for n in neighbors(c, EDGE):
            if n not in place and cells[n] == who:
                return False
    if has_own(cells, who):
        corner_ok = False
        for c in place:
            for n in neighbors(c, CORNER):
                if cells[n] == who:
                    corner_ok = True
                    break
            if corner_ok:
                break
        if not corner_ok:
            return False
    else:
        corners = {0, N - 1, N * (N - 1), N * N - 1}
        if not any(c in corners for c in place):
            return False
    return True


def all_placements(
    cells: tuple[int, ...], who: int, inv: tuple[str, ...]
) -> list[tuple[str, tuple[int, ...]]]:
    out: list[tuple[str, tuple[int, ...]]] = []
    seen: set[tuple[str, tuple[int, ...]]] = set()
    for pid in inv:
        if pid not in ORIENTS:
            continue
        for oi in range(len(ORIENTS[pid])):
            for a in range(N * N):
                place = squares_of(pid, a, oi)
                if place is None:
                    continue
                key = (pid, place)
                if key in seen:
                    continue
                if legal_on(cells, who, pid, place):
                    seen.add(key)
                    out.append(key)
    return out


def apply(
    cells: tuple[int, ...],
    who: int,
    pid: str,
    place: tuple[int, ...],
    inv: tuple[str, ...],
) -> tuple[tuple[int, ...], tuple[str, ...]]:
    if pid not in inv:
        raise ValueError("piece not in inventory")
    if not legal_on(cells, who, pid, place):
        raise ValueError("illegal")
    board = list(cells)
    for c in place:
        board[c] = who
    ninv = list(inv)
    ninv.remove(pid)
    return tuple(board), tuple(ninv)


def sq_left(inv: tuple[str, ...]) -> int:
    return sum(SIZE[p] for p in inv if p in SIZE)


def filled(inv: tuple[str, ...]) -> bool:
    return sq_left(inv) <= FLOOR


@cache
def can_force(
    cells: tuple[int, ...],
    binv: tuple[str, ...],
    yinv: tuple[str, ...],
    stones: int,
) -> bool:
    if filled(binv):
        return True
    if stones <= 0:
        return False
    moves = all_placements(cells, BLUE, binv)
    if not moves:
        return filled(binv)
    for pid, place in moves:
        after, nb = apply(cells, BLUE, pid, place, binv)
        if filled(nb):
            return True
        if stones == 1:
            continue
        ymoves = all_placements(after, YELLOW, yinv)
        if not ymoves:
            if can_force(after, nb, yinv, stones - 1):
                return True
            continue
        ok = True
        for yp, ypl in ymoves:
            ya, ny = apply(after, YELLOW, yp, ypl, yinv)
            if not can_force(ya, nb, ny, stones - 1):
                ok = False
                break
        if ok:
            return True
    return False


@cache
def can_coop(
    cells: tuple[int, ...],
    binv: tuple[str, ...],
    yinv: tuple[str, ...],
    stones: int,
) -> bool:
    if filled(binv):
        return True
    if stones <= 0:
        return False
    for pid, place in all_placements(cells, BLUE, binv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        if filled(nb) or can_coop(after, nb, yinv, stones - 1):
            return True
    return False


def verdict(
    cells: tuple[int, ...], binv: tuple[str, ...], yinv: tuple[str, ...]
) -> str:
    can_force.cache_clear()
    can_coop.cache_clear()
    if can_force(cells, binv, yinv, BUDGET):
        return "win"
    if can_coop(cells, binv, yinv, BUDGET):
        return "trap"
    return "fort"


def threats(
    cells: tuple[int, ...], binv: tuple[str, ...], yinv: tuple[str, ...]
) -> list[tuple[str, tuple[int, ...]]]:
    out: list[tuple[str, tuple[int, ...]]] = []
    for pid, place in all_placements(cells, BLUE, binv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        if filled(nb):
            continue
        for pid2, place2 in all_placements(after, BLUE, nb):
            _after2, nb2 = apply(after, BLUE, pid2, place2, nb)
            if filled(nb2):
                out.append((pid, place))
                break
    return out


def forcing_first_moves(
    cells: tuple[int, ...], binv: tuple[str, ...], yinv: tuple[str, ...]
) -> set[str]:
    out: set[str] = set()
    for pid, place in all_placements(cells, BLUE, binv):
        after, nb = apply(cells, BLUE, pid, place, binv)
        if filled(nb):
            out.add(fmt_placement(pid, place))
            continue
        ymoves = all_placements(after, YELLOW, yinv)
        if not ymoves:
            if can_force(after, nb, yinv, BUDGET - 1):
                out.add(fmt_placement(pid, place))
            continue
        ok = True
        for yp, ypl in ymoves:
            ya, ny = apply(after, YELLOW, yp, ypl, yinv)
            if not can_force(ya, nb, ny, BUDGET - 1):
                ok = False
                break
        if ok:
            out.add(fmt_placement(pid, place))
    return out


def read_sheet(path: Path):
    board_id = ""
    binv: list[str] = []
    yinv: list[str] = []
    rows: list[str] = []
    started = False
    for raw in path.read_text().splitlines():
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith("board_id:"):
            board_id = text.split(":", 1)[1].strip()
        elif text.startswith("blue_inv:"):
            raw_inv = text.split(":", 1)[1].strip()
            binv = [x.strip() for x in raw_inv.split(",") if x.strip()]
        elif text.startswith("yellow_inv:"):
            raw_inv = text.split(":", 1)[1].strip()
            yinv = [x.strip() for x in raw_inv.split(",") if x.strip()]
        elif text == "board:" or text.startswith("board:"):
            started = True
            rest = text.split(":", 1)[1].strip() if ":" in text else ""
            if rest:
                rows.append(rest)
        elif started and len(text) == N and len(rows) < N:
            rows.append(text)
    assert len(rows) == N, f"{path} grid is not {N} rows"
    cells = [EMPTY] * (N * N)
    for offset, row in enumerate(rows):
        rank = N - 1 - offset
        for index, disc in enumerate(row):
            cells[rank * N + index] = {
                ".": EMPTY,
                "B": BLUE,
                "Y": YELLOW,
                "X": BLOCK,
            }[disc]
    return board_id, tuple(cells), tuple(binv), tuple(yinv)


_SHEETS: dict[str, tuple] = {}


def sheets() -> dict[str, tuple]:
    if not _SHEETS:
        for path in sorted(SHEETS.glob("board_*.txt")):
            board_id, cells, binv, yinv = read_sheet(path)
            _SHEETS[board_id] = (cells, binv, yinv, path)
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


def judge_legal(path: Path, side: str) -> list[str]:
    seen = subprocess.run(
        [
            "java",
            "-jar",
            str(JUDGE),
            "legal",
            "--board",
            str(path),
            "--side",
            side,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert seen.returncode == 0, f"judge legal failed: {seen.stdout}{seen.stderr}"
    body = json.loads(seen.stdout)
    legal = body.get("legal")
    assert isinstance(legal, list), "judge legal must return a list"
    return [str(x) for x in legal]


def parse_step(step: str):
    assert isinstance(step, str), "a sequence step must be a string"
    head, _, tail = step.strip().partition(" ")
    assert head in ("blue", "yellow"), f"step {step!r} needs a colour word"
    return head, parse_placement(tail.strip())


def _defeats_threat(
    cells: tuple[int, ...],
    binv: tuple[str, ...],
    yinv: tuple[str, ...],
    pid: str,
    place: tuple[int, ...],
    reply: str,
) -> bool:
    if (pid, place) not in all_placements(cells, BLUE, binv):
        return False
    after, nb = apply(cells, BLUE, pid, place, binv)
    if filled(nb):
        return False
    try:
        yp, ypl = parse_placement(reply)
    except ValueError:
        return False
    if (yp, ypl) not in all_placements(after, YELLOW, yinv):
        return False
    held, _ny = apply(after, YELLOW, yp, ypl, yinv)
    return not any(
        filled(apply(held, BLUE, p2, pl2, nb)[1])
        for p2, pl2 in all_placements(held, BLUE, nb)
    )


def forcing_ok(
    cells: tuple[int, ...],
    binv: tuple[str, ...],
    yinv: tuple[str, ...],
    sequence: list[str],
) -> bool:
    """Every Blue placement in the line must keep the floor forced with turns left."""
    if not sequence:
        return False
    who = BLUE
    stones = BUDGET
    cur = cells
    bi, yi = binv, yinv
    for step in sequence:
        # Yellow passes (omitted from the filed line) when it has nothing legal.
        while who == YELLOW and not all_placements(cur, YELLOW, yi):
            who = BLUE
        colour, (pid, place) = parse_step(step)
        expect = "blue" if who == BLUE else "yellow"
        if colour != expect:
            return False
        inv = bi if who == BLUE else yi
        if (pid, place) not in all_placements(cur, who, inv):
            return False
        if who == BLUE:
            if stones <= 0:
                return False
            after, nb = apply(cur, who, pid, place, bi)
            if not filled(nb):
                replies = all_placements(after, YELLOW, yi)
                if replies:
                    held = True
                    for yp, ypl in replies:
                        ya, ny = apply(after, YELLOW, yp, ypl, yi)
                        if not can_force(ya, nb, ny, stones - 1):
                            held = False
                            break
                    if not held:
                        return False
                elif not can_force(after, nb, yi, stones - 1):
                    return False
            cur = after
            bi = nb
            stones -= 1
            if filled(bi):
                return True
        else:
            cur, yi = apply(cur, who, pid, place, yi)
            if filled(bi):
                return True
        who = YELLOW if who == BLUE else BLUE
    return filled(bi)


def friendly_ok(
    cells: tuple[int, ...],
    binv: tuple[str, ...],
    yinv: tuple[str, ...],
    sequence: list[str],
) -> bool:
    if not sequence or len(sequence) > BUDGET:
        return False
    cur = cells
    bi = binv
    for step in sequence:
        colour, (pid, place) = parse_step(step)
        if colour != "blue":
            return False
        if (pid, place) not in all_placements(cur, BLUE, bi):
            return False
        cur, bi = apply(cur, BLUE, pid, place, bi)
        if filled(bi):
            return True
    return False


def refutations_ok(
    cells: tuple[int, ...],
    binv: tuple[str, ...],
    yinv: tuple[str, ...],
    rows: list,
) -> bool:
    wanted = threats(cells, binv, yinv)
    if not wanted:
        return False
    filed: list[tuple[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            return False
        piece_id, reply = row.get("piece_id"), row.get("reply")
        if not isinstance(piece_id, str) or not isinstance(reply, str):
            return False
        filed.append((piece_id, reply))
    for pid, place in wanted:
        if not any(
            piece_id == pid and _defeats_threat(cells, binv, yinv, pid, place, reply)
            for piece_id, reply in filed
        ):
            return False
    # Extra rows must still be real threat answers.
    threat_keys = {(pid, place) for pid, place in wanted}
    for piece_id, reply in filed:
        matched = False
        for pid, place in threat_keys:
            if pid != piece_id:
                continue
            if _defeats_threat(cells, binv, yinv, pid, place, reply):
                matched = True
                break
        if not matched:
            # Allow extras that defeat some same-piece threat even if duplicate.
            for pid, place in all_placements(cells, BLUE, binv):
                if pid != piece_id:
                    continue
                after, nb = apply(cells, BLUE, pid, place, binv)
                if filled(nb):
                    continue
                if any(
                    filled(apply(after, BLUE, p2, pl2, nb)[1])
                    for p2, pl2 in all_placements(after, BLUE, nb)
                ) and _defeats_threat(cells, binv, yinv, pid, place, reply):
                    matched = True
                    break
        if not matched:
            return False
    return True


def round_ok(board_id: str, row: dict) -> bool:
    cells, binv, yinv, path = sheets()[board_id]
    want = verdict(cells, binv, yinv)
    if row.get("status") != want:
        return False
    if bool(row.get("coop_fill")) != (want != "fort"):
        return False
    sequence = row.get("sequence")
    if not isinstance(sequence, list):
        return False
    refutations = row.get("refutations")
    if not isinstance(refutations, list):
        return False
    piece_id = row.get("piece_id")
    placement = row.get("placement")
    squares_left = row.get("squares_left")
    if want == "fort":
        return (
            sequence == []
            and refutations == []
            and piece_id == ""
            and placement == ""
            and squares_left == sq_left(binv)
        )
    if not isinstance(piece_id, str) or not isinstance(placement, str):
        return False
    if not isinstance(squares_left, int):
        return False
    opening = f"{piece_id}@{placement}"
    if want == "win":
        if refutations:
            return False
        if opening not in forcing_first_moves(cells, binv, yinv):
            return False
        if not forcing_ok(cells, binv, yinv, [str(s) for s in sequence]):
            return False
        seen = judge_line(path, [str(s) for s in sequence])
        return (
            seen["all_legal"]
            and seen["filled"]
            and seen["squares_left"] == squares_left
            and seen["blue_turns"] <= BUDGET
            and sequence
            and sequence[0] == f"blue {opening}"
        )
    # trap
    if not friendly_ok(cells, binv, yinv, [str(s) for s in sequence]):
        return False
    if not refutations_ok(cells, binv, yinv, refutations):
        return False
    if not sequence or sequence[0] != f"blue {opening}":
        return False
    seen = judge_line(path, [str(s) for s in sequence])
    return (
        seen["all_legal"]
        and seen["filled"]
        and seen["squares_left"] == squares_left
        and seen["blue_turns"] <= BUDGET
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
        assert isinstance(row.get("sequence"), list), (
            f"round {board_id} sequence must be a list"
        )
        assert isinstance(row.get("refutations"), list), (
            f"round {board_id} refutations must be a list"
        )
        assert isinstance(row.get("coop_fill"), bool), (
            f"round {board_id} coop_fill must be bool"
        )
        assert isinstance(row.get("piece_id"), str), (
            f"round {board_id} piece_id must be a string"
        )
        assert isinstance(row.get("placement"), str), (
            f"round {board_id} placement must be a string"
        )
        assert isinstance(row.get("squares_left"), int), (
            f"round {board_id} squares_left must be an int"
        )
        if status == "fort":
            assert row["sequence"] == [], f"fort round {board_id} carries a sequence"
            assert row["piece_id"] == "", f"fort round {board_id} carries a piece_id"
            assert row["placement"] == "", f"fort round {board_id} carries a placement"
        else:
            assert row["sequence"], f"{status} round {board_id} carries no sequence"
            assert row["piece_id"], f"{status} round {board_id} carries no piece_id"
            assert row["placement"], f"{status} round {board_id} carries no placement"
            assert row["sequence"][0] == f"blue {row['piece_id']}@{row['placement']}"
        if status != "trap":
            assert row["refutations"] == [], (
                f"{status} round {board_id} carries refutations"
            )
    filed = {row["status"] for row in rounds.values()}
    assert filed == set(VERDICTS), f"card only uses {sorted(filed)}"


def test_c3_slate_filed_sequences_replay_past_the_sealed_judge():
    """The table replays every sequence: legal placements, floor met, squares match."""
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
        _, _, _, path = sheets()[board_id]
        steps = [str(s) for s in row["sequence"]]
        try:
            seen = judge_line(path, steps)
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
        if (
            seen["all_legal"]
            and seen["filled"]
            and seen["squares_left"] == row.get("squares_left")
            and seen["blue_turns"] <= BUDGET
        ):
            ok += 1
    assert ok >= len(carried) - 1, f"judge accepted {ok}/{len(carried)} filed sequences"


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Verdict words must survive an independent replay of the booklet."""
    rounds = card_rounds()
    ok = 0
    for board_id, (cells, binv, yinv, _) in sorted(sheets().items()):
        row = rounds.get(board_id, {})
        want = verdict(cells, binv, yinv)
        if row.get("status") == want and bool(row.get("coop_fill")) == (want != "fort"):
            ok += 1
    assert ok >= 9, f"verdicts agree on {ok}/10 rounds"


def test_g2_flint_forcing_sequences_really_force():
    """A win sequence has to hold up against every Yellow reply, not a soft one."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, binv, yinv, _) in sorted(sheets().items())
        if verdict(cells, binv, yinv) == "win"
    ]
    ok = 0
    for board_id in wanted:
        cells, binv, yinv, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "win":
            continue
        sequence = row.get("sequence")
        piece_id = row.get("piece_id")
        placement = row.get("placement")
        if (
            not isinstance(sequence, list)
            or not isinstance(piece_id, str)
            or not isinstance(placement, str)
        ):
            continue
        opening = f"{piece_id}@{placement}"
        try:
            if opening in forcing_first_moves(cells, binv, yinv) and forcing_ok(
                cells, binv, yinv, [str(s) for s in sequence]
            ):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} win sequences force the floor"


def test_j4_amber_friendly_sequences_reach_the_floor():
    """Trap sequences are Blue alone inside three placements with Yellow sitting still."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, binv, yinv, _) in sorted(sheets().items())
        if verdict(cells, binv, yinv) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        cells, binv, yinv, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "trap":
            continue
        sequence = row.get("sequence")
        if not isinstance(sequence, list):
            continue
        try:
            if friendly_ok(cells, binv, yinv, [str(s) for s in sequence]):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} friendly sequences reach the floor"


def test_k7_topaz_refutations_cover_every_threat():
    """Yellow must answer each inventory-wasting threat, and only real answers count."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (cells, binv, yinv, _) in sorted(sheets().items())
        if verdict(cells, binv, yinv) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        cells, binv, yinv, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        rows = row.get("refutations")
        if row.get("status") != "trap" or not isinstance(rows, list):
            continue
        try:
            if refutations_ok(cells, binv, yinv, rows):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} trap rounds fully refuted"


def test_m8_jade_forts_are_not_the_kiosk_cheer():
    """The kiosk stamps a win wherever a fourth placement reaches; the table does not."""
    rounds = card_rounds()
    forts = [
        board_id
        for board_id, (cells, binv, yinv, _) in sorted(sheets().items())
        if verdict(cells, binv, yinv) == "fort"
    ]
    assert forts, "booklet lost its fort rounds"
    held = sum(1 for board_id in forts if rounds.get(board_id, {}).get("status") == "fort")
    assert held >= len(forts) - 1, f"{held}/{len(forts)} fort rounds filed as forts"
    optimistic = sum(1 for row in rounds.values() if row.get("status") == "win")
    assert optimistic < len(rounds), "every round filed as a win"
    for board_id in forts:
        cells, binv, yinv, _ = sheets()[board_id]
        assert not can_coop(cells, binv, yinv, BUDGET), (
            f"fort {board_id} still coop-fills inside three Blue placements"
        )


def test_n2_coral_squares_left_is_not_padded():
    """Filed squares_left must match the sealed judge after the sequence, not a padded boast."""
    rounds = card_rounds()
    ok = 0
    checked = 0
    for board_id, row in sorted(rounds.items()):
        sequence = row.get("sequence")
        if not isinstance(sequence, list) or not sequence:
            continue
        checked += 1
        _, _, _, path = sheets()[board_id]
        try:
            seen = judge_line(path, [str(s) for s in sequence])
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
        if seen.get("squares_left") == row.get("squares_left") and seen.get("filled"):
            ok += 1
    assert checked >= 8
    assert ok >= checked - 1, f"squares_left matched on {ok}/{checked} sequenced rounds"


def test_p5_quartz_whole_booklet_stands_up():
    """Near-exact booklet: verdict, play, refutations, and squares_left together."""
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
    body = json.loads(CARD.read_text())
    staged = tmp_path / "blokus-card.json"
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


def test_w3_garnet_edge_touch_is_illegal_for_same_colour():
    """Same-colour edge contact must never appear in the sealed legal list."""
    assert JUDGE.is_file(), "sealed judge missing"
    baits = 0
    for board_id, (cells, binv, yinv, path) in sorted(sheets().items()):
        for side, who, inv in (("blue", BLUE, binv), ("yellow", YELLOW, yinv)):
            if not inv:
                continue
            legal = set(judge_legal(path, side))
            for token in legal:
                pid, place = parse_placement(token)
                assert legal_on(cells, who, pid, place), (
                    f"{board_id} {side} listed illegal {token}"
                )
                for c in place:
                    for n in neighbors(c, EDGE):
                        if n not in place:
                            assert cells[n] != who, (
                                f"{board_id} {side} edge-touches own colour via {token}"
                            )
            for pid in inv:
                if pid not in ORIENTS:
                    continue
                for oi in range(len(ORIENTS[pid])):
                    for a in range(N * N):
                        place = squares_of(pid, a, oi)
                        if place is None:
                            continue
                        if any(cells[c] != EMPTY for c in place):
                            continue
                        edge_touch = any(
                            cells[n] == who
                            for c in place
                            for n in neighbors(c, EDGE)
                            if n not in place
                        )
                        if not edge_touch:
                            continue
                        token = fmt_placement(pid, place)
                        assert token not in legal, (
                            f"{board_id} {side} admits edge-touch {token}"
                        )
                        baits += 1
    assert baits >= 10, f"only {baits} edge-touch baits checked"
