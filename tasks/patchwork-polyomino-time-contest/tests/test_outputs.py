"""Verifier for the patch-market tournament booklet.

Rebuilds every verdict from the round sheets with its own two-player search and
replays each filed line past a pristine copy of the sealed table judge. Nothing
here trusts the card: statuses, forcing lines, cooperative lines, refutations,
and the first-pick economy readouts are all recomputed from the sheets.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

CARD = Path("/output/patchwork-card.json")
SHEETS = Path("/app/puzzles")
JUDGE = Path("/opt/tbench/judge.jar")
LIVE_JUDGE = Path("/app/bin/judge.jar")
# Pristine copy of the overnight printer, staged read-only by the image so the
# determinism check does not depend on the agent-editable /app/kiosk copy.
EMIT = Path("/opt/tbench/kiosk/emit_card.sh")
VERDICTS = ("win", "trap", "fort")


# ---------------------------------------------------------------------------
# round sheet model + independent engine
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Patch:
    pid: str
    time: int
    cost: int
    income: int
    cells: tuple[tuple[int, int], ...]

    @property
    def size(self) -> int:
        return len(self.cells)


@dataclass(frozen=True)
class Board:
    board_id: str
    rows: int
    cols: int
    blocked: frozenset
    track: int
    income: tuple[int, ...]
    floor: int
    red_start: int
    blue_start: int
    patches: tuple[Patch, ...]

    @property
    def area(self) -> int:
        return self.rows * self.cols

    def patch(self, pid: str) -> Patch:
        for p in self.patches:
            if p.pid == pid:
                return p
        raise KeyError(pid)


def _cell_of(token: str, cols: int) -> int:
    token = token.strip().lower()
    r = int(token[token.index("r") + 1 : token.index("c")])
    c = int(token[token.index("c") + 1 :])
    return r * cols + c


def _shape_cells(shape: str) -> tuple[tuple[int, int], ...]:
    pts = []
    for r, row in enumerate(shape.split("/")):
        for c, ch in enumerate(row):
            if ch == "X":
                pts.append((r, c))
    minr = min(p[0] for p in pts)
    minc = min(p[1] for p in pts)
    return tuple(sorted((r - minr, c - minc) for r, c in pts))


def parse_board(text: str) -> Board:
    board_id = ""
    rows = cols = track = floor = red_start = blue_start = 0
    blocked: set = set()
    income: tuple = ()
    patches: list = []
    in_market = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if in_market:
            head, _, shape = line.partition(":")
            f = head.split()
            patches.append(
                Patch(f[0], int(f[1]), int(f[2]), int(f[3]), _shape_cells(shape.strip()))
            )
            continue
        if line.startswith("board_id:"):
            board_id = line.split(":", 1)[1].strip()
        elif line.startswith("quilt:"):
            rc = line.split(":", 1)[1].strip().lower().split("x")
            rows, cols = int(rc[0]), int(rc[1])
        elif line.startswith("blocked:"):
            for tok in line.split(":", 1)[1].split(","):
                tok = tok.strip()
                if tok:
                    blocked.add(_cell_of(tok, cols))
        elif line.startswith("time_track:"):
            track = int(line.split(":", 1)[1].strip())
        elif line.startswith("income:"):
            income = tuple(int(x) for x in line.split(":", 1)[1].split(",") if x.strip())
        elif line.startswith("floor:"):
            floor = int(line.split(":", 1)[1].strip())
        elif line.startswith("red_start:"):
            red_start = int(line.split(":", 1)[1].strip())
        elif line.startswith("blue_start:"):
            blue_start = int(line.split(":", 1)[1].strip())
        elif line == "market:":
            in_market = True
    return Board(
        board_id, rows, cols, frozenset(blocked), track, income, floor,
        red_start, blue_start, tuple(patches),
    )


_FIT: dict = {}


def fit(board: Board, taken: frozenset) -> bool:
    key = (board.board_id, taken)
    if key in _FIT:
        return _FIT[key]
    order = sorted(taken, key=lambda p: (-board.patch(p).size, p))
    occupied = set(board.blocked)

    def place(idx: int) -> bool:
        if idx == len(order):
            return True
        patch = board.patch(order[idx])
        for anchor in range(board.area):
            ar, ac = divmod(anchor, board.cols)
            cells = []
            ok = True
            for dr, dc in patch.cells:
                rr, cc = ar + dr, ac + dc
                if not (0 <= rr < board.rows and 0 <= cc < board.cols):
                    ok = False
                    break
                pos = rr * board.cols + cc
                if pos in occupied:
                    ok = False
                    break
                cells.append(pos)
            if not ok:
                continue
            occupied.update(cells)
            if place(idx + 1):
                return True
            occupied.difference_update(cells)
        return False

    result = place(0)
    _FIT[key] = result
    return result


def initial(board: Board):
    return (0, board.red_start, frozenset(), 0, board.blue_start, frozenset())


def _rate(board: Board, taken: frozenset) -> int:
    return sum(board.patch(p).income for p in taken)


def _crossed(board: Board, t0: int, t1: int, rate: int) -> int:
    return rate * sum(1 for s in board.income if t0 < s <= t1)


def market(board: Board, st) -> frozenset:
    _, _, red_taken, _, _, blue_taken = st
    return frozenset(p.pid for p in board.patches) - red_taken - blue_taken


def to_move(board: Board, st):
    rt, _, _, bt, _, _ = st
    if rt == board.track and bt == board.track:
        return None
    if rt < bt:
        return "R"
    if bt < rt:
        return "B"
    return "R"


def red_moves(board: Board, st):
    _, rb, red_taken, _, _, _ = st
    moves = [("R", "adv")]
    for pid in sorted(market(board, st)):
        patch = board.patch(pid)
        if patch.cost <= rb and fit(board, red_taken | {pid}):
            moves.append(("R", "take", pid))
    return moves


def blue_moves(board: Board, st):
    _, _, _, _, bb, _ = st
    moves = [("B", "adv")]
    for pid in sorted(market(board, st)):
        if board.patch(pid).cost <= bb:
            moves.append(("B", "take", pid))
    return moves


def legal_moves(board: Board, st):
    side = to_move(board, st)
    if side == "R":
        return red_moves(board, st)
    if side == "B":
        return blue_moves(board, st)
    return []


def apply_move(board: Board, st, move):
    rt, rb, red_taken, bt, bb, blue_taken = st
    if move[0] == "R":
        if move[1] == "adv":
            new_rt = min(board.track, bt + 1)
            gain = (new_rt - rt) + _crossed(board, rt, new_rt, _rate(board, red_taken))
            return (new_rt, rb + gain, red_taken, bt, bb, blue_taken)
        patch = board.patch(move[2])
        new_taken = red_taken | {move[2]}
        new_rt = min(board.track, rt + patch.time)
        new_rb = rb - patch.cost + _crossed(board, rt, new_rt, _rate(board, new_taken))
        return (new_rt, new_rb, new_taken, bt, bb, blue_taken)
    if move[1] == "adv":
        new_bt = min(board.track, rt + 1)
        gain = (new_bt - bt) + _crossed(board, bt, new_bt, _rate(board, blue_taken))
        return (rt, rb, red_taken, new_bt, bb + gain, blue_taken)
    patch = board.patch(move[2])
    new_taken = blue_taken | {move[2]}
    new_bt = min(board.track, bt + patch.time)
    new_bb = bb - patch.cost + _crossed(board, bt, new_bt, _rate(board, new_taken))
    return (rt, rb, red_taken, new_bt, new_bb, new_taken)


def terminal(board: Board, st) -> bool:
    return to_move(board, st) is None


def red_score(board: Board, st) -> int:
    _, rb, red_taken, _, _, _ = st
    covered = sum(board.patch(p).size for p in red_taken)
    return rb - 2 * (board.area - len(board.blocked) - covered)


_SOLVERS: dict = {}


def _solver(board: Board):
    if board.board_id in _SOLVERS:
        return _SOLVERS[board.board_id]

    @cache
    def forced(st) -> bool:
        if terminal(board, st):
            return red_score(board, st) >= board.floor
        side = to_move(board, st)
        kids = [apply_move(board, st, m) for m in legal_moves(board, st)]
        return any(forced(k) for k in kids) if side == "R" else all(forced(k) for k in kids)

    @cache
    def coop(st) -> bool:
        if terminal(board, st):
            return red_score(board, st) >= board.floor
        if to_move(board, st) == "R":
            return any(coop(apply_move(board, st, m)) for m in red_moves(board, st))
        return coop(apply_move(board, st, ("B", "adv")))

    _SOLVERS[board.board_id] = (forced, coop)
    return forced, coop


def verdict(board: Board) -> str:
    forced, coop = _solver(board)
    st0 = initial(board)
    if forced(st0):
        return "win"
    if coop(st0):
        return "trap"
    return "fort"


def candidate_first_takes(board: Board):
    return [m[2] for m in red_moves(board, initial(board)) if m[1] == "take"]


def parse_step(step: str):
    parts = str(step).strip().split()
    side = {"red": "R", "blue": "B"}.get(parts[0])
    if side is None:
        raise ValueError(step)
    if parts[1] == "advance":
        return (side, "adv")
    if parts[1] == "take":
        return (side, "take", parts[2])
    raise ValueError(step)


# ---------------------------------------------------------------------------
# line validators (independent of exact placement; placement is the judge's job)
# ---------------------------------------------------------------------------


def forcing_ok(board: Board, seq) -> bool:
    if not seq:
        return False
    forced, _ = _solver(board)
    st = initial(board)
    for step in seq:
        move = parse_step(step)
        side = to_move(board, st)
        if side is None or move[0] != side:
            return False
        if move not in legal_moves(board, st):
            return False
        st = apply_move(board, st, move)
        if move[0] == "R" and not forced(st):
            return False
    return terminal(board, st) and red_score(board, st) >= board.floor


def coop_ok(board: Board, seq) -> bool:
    if not seq:
        return False
    st = initial(board)
    for step in seq:
        move = parse_step(step)
        side = to_move(board, st)
        if side is None or move[0] != side:
            return False
        if move[0] == "B" and move != ("B", "adv"):
            return False
        if move not in legal_moves(board, st):
            return False
        st = apply_move(board, st, move)
    return terminal(board, st) and red_score(board, st) >= board.floor


def refutations_ok(board: Board, rows) -> bool:
    wanted = set(candidate_first_takes(board))
    if not wanted:
        return False
    forced, _ = _solver(board)
    filed: dict = {}
    for row in rows:
        if not isinstance(row, dict):
            return False
        pid, reply = row.get("patch_id"), row.get("reply")
        if not isinstance(pid, str) or not isinstance(reply, str) or pid in filed:
            return False
        filed[pid] = reply
    if set(filed) != wanted:
        return False
    for pid, reply in filed.items():
        st1 = apply_move(board, initial(board), ("R", "take", pid))
        parts = reply.split()
        if parts[0] == "advance":
            move = ("B", "adv")
        elif parts[0] == "take" and len(parts) >= 2:
            move = ("B", "take", parts[1])
        else:
            return False
        if move not in blue_moves(board, st1):
            return False
        if forced(apply_move(board, st1, move)):
            return False
    return True


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

_SHEETS: dict = {}


def sheets() -> dict:
    if not _SHEETS:
        for path in sorted(SHEETS.glob("board_*.txt")):
            board = parse_board(path.read_text())
            _SHEETS[board.board_id] = (board, path)
    return _SHEETS


def card_rounds() -> dict:
    assert CARD.is_file(), f"{CARD} was never filed"
    body = json.loads(CARD.read_text())
    assert isinstance(body, dict), "card must be a JSON object"
    rounds = body.get("rounds")
    assert isinstance(rounds, list), "card needs a rounds list"
    out: dict = {}
    for row in rounds:
        assert isinstance(row, dict), "each round must be an object"
        board_id = row.get("board_id")
        assert isinstance(board_id, str), "each round needs a board_id"
        assert board_id not in out, f"round {board_id} filed twice"
        out[board_id] = row
    return out


def judge_line(path: Path, seq) -> dict:
    seen = subprocess.run(
        ["java", "-jar", str(JUDGE), "validate", "--board", str(path),
         "--line", ";".join(str(s) for s in seq)],
        capture_output=True, text=True, check=False,
    )
    assert seen.returncode == 0, f"judge refused the line: {seen.stdout}{seen.stderr}"
    return json.loads(seen.stdout)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_a1_onyx_card_reads_as_a_tournament_card():
    """Ten rounds, table verdict words, and empty fields only where allowed."""
    rounds = card_rounds()
    assert set(rounds) == set(sheets()), (
        f"card covers {sorted(rounds)}; booklet has {sorted(sheets())}"
    )
    for board_id, row in rounds.items():
        status = row.get("status")
        assert status in VERDICTS, f"round {board_id} status {status!r}"
        assert isinstance(row.get("sequence"), list), f"round {board_id} sequence must be a list"
        assert isinstance(row.get("refutations"), list), f"round {board_id} refutations must be a list"
        assert isinstance(row.get("coop_fill"), bool), f"round {board_id} coop_fill must be bool"
        assert isinstance(row.get("patch_id"), str), f"round {board_id} patch_id must be a string"
        assert isinstance(row.get("time_cost"), int), f"round {board_id} time_cost must be int"
        assert isinstance(row.get("buttons"), int), f"round {board_id} buttons must be int"
        if status == "fort":
            assert row["sequence"] == [], f"fort round {board_id} carries a line"
            assert row["refutations"] == [], f"fort round {board_id} carries refutations"
            assert row["patch_id"] == "", f"fort round {board_id} names a first pick"
        else:
            assert row["sequence"], f"{status} round {board_id} carries no line"
        if status != "trap":
            assert row["refutations"] == [], f"{status} round {board_id} carries refutations"
    filed = {row["status"] for row in rounds.values()}
    assert filed == set(VERDICTS), f"card only uses {sorted(filed)}"


def test_c3_slate_filed_lines_replay_past_the_sealed_judge():
    """The table replays every filed line: legal turns, reaching the floor."""
    assert LIVE_JUDGE.is_file(), "the sealed judge left the table"
    assert LIVE_JUDGE.read_bytes() == JUDGE.read_bytes(), "the sealed judge was altered"
    rounds = card_rounds()
    carried = [
        (bid, row)
        for bid, row in sorted(rounds.items())
        if isinstance(row.get("sequence"), list) and row["sequence"]
    ]
    assert len(carried) >= 6, f"only {len(carried)} rounds carry a line"
    ok = 0
    for bid, row in carried:
        _, path = sheets()[bid]
        try:
            seen = judge_line(path, row["sequence"])
        except (AssertionError, ValueError):
            continue
        if (
            seen["all_legal"]
            and seen["terminal"]
            and seen["floor_met"]
            and seen["red_first_patch"] == row.get("patch_id")
        ):
            ok += 1
    assert ok >= len(carried) - 1, f"judge accepted {ok}/{len(carried)} filed lines"


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Verdict words must survive an independent two-player replay."""
    rounds = card_rounds()
    ok = 0
    for bid, (board, _) in sorted(sheets().items()):
        if rounds.get(bid, {}).get("status") == verdict(board):
            ok += 1
    assert ok >= len(sheets()) - 1, f"verdicts agree on {ok}/{len(sheets())} rounds"


def test_g2_flint_win_lines_really_force():
    """A win line must hold against every Blue denial, not a soft one."""
    rounds = card_rounds()
    wanted = [bid for bid, (b, _) in sorted(sheets().items()) if verdict(b) == "win"]
    ok = 0
    for bid in wanted:
        board, _ = sheets()[bid]
        row = rounds.get(bid, {})
        if row.get("status") != "win":
            continue
        try:
            if forcing_ok(board, row.get("sequence") or []):
                ok += 1
        except (AssertionError, ValueError, KeyError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} win lines force the floor"


def test_j4_amber_trap_lines_reach_the_floor():
    """Trap lines reach the floor while Blue keeps advancing."""
    rounds = card_rounds()
    wanted = [bid for bid, (b, _) in sorted(sheets().items()) if verdict(b) == "trap"]
    ok = 0
    for bid in wanted:
        board, _ = sheets()[bid]
        row = rounds.get(bid, {})
        if row.get("status") != "trap":
            continue
        try:
            if coop_ok(board, row.get("sequence") or []):
                ok += 1
        except (AssertionError, ValueError, KeyError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} trap lines reach the floor"


def test_k7_topaz_refutations_cover_every_opening():
    """Blue must answer each takeable opening on a trap round, and only real ones."""
    rounds = card_rounds()
    wanted = [bid for bid, (b, _) in sorted(sheets().items()) if verdict(b) == "trap"]
    ok = 0
    for bid in wanted:
        board, _ = sheets()[bid]
        row = rounds.get(bid, {})
        rows = row.get("refutations")
        if row.get("status") != "trap" or not isinstance(rows, list):
            continue
        try:
            if refutations_ok(board, rows):
                ok += 1
        except (AssertionError, ValueError, KeyError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} trap rounds fully refuted"


def test_m8_jade_forts_are_not_the_kiosk_cheer():
    """The kiosk stamps a win wherever an idle Blue helps; the table does not."""
    rounds = card_rounds()
    forts = [bid for bid, (b, _) in sorted(sheets().items()) if verdict(b) == "fort"]
    assert forts, "booklet lost its fort rounds"
    held = sum(1 for bid in forts if rounds.get(bid, {}).get("status") == "fort")
    assert held >= len(forts) - 1, f"{held}/{len(forts)} fort rounds filed as forts"
    optimistic = sum(1 for row in rounds.values() if row.get("status") == "win")
    assert optimistic < len(rounds), "every round filed as a win"


def test_n2_coral_first_pick_readouts_match_the_market():
    """time_cost and buttons on a filed round must be the opening patch's own stats."""
    rounds = card_rounds()
    carried = [bid for bid, (b, _) in sorted(sheets().items()) if verdict(b) != "fort"]
    ok = 0
    for bid in carried:
        board, _ = sheets()[bid]
        row = rounds.get(bid, {})
        pid = row.get("patch_id")
        try:
            patch = board.patch(pid)
        except (KeyError, TypeError):
            continue
        if row.get("time_cost") == patch.time and row.get("buttons") == patch.income:
            ok += 1
    assert ok >= len(carried) - 1, f"{ok}/{len(carried)} first-pick readouts match the market"


def test_p5_quartz_whole_booklet_stands_up():
    """Near-exact booklet: verdict, coop_fill, play, and refutations together."""
    rounds = card_rounds()
    ok = 0
    for bid, (board, path) in sorted(sheets().items()):
        row = rounds.get(bid)
        if not isinstance(row, dict):
            continue
        try:
            want = verdict(board)
            if row.get("status") != want:
                continue
            if row.get("coop_fill") != (want != "fort"):
                continue
            if want == "fort":
                good = row.get("sequence") == [] and row.get("refutations") == []
            elif want == "win":
                good = (
                    not row.get("refutations")
                    and forcing_ok(board, row.get("sequence") or [])
                    and judge_line(path, row["sequence"])["all_legal"]
                )
            else:
                good = (
                    coop_ok(board, row.get("sequence") or [])
                    and refutations_ok(board, row.get("refutations") or [])
                    and judge_line(path, row["sequence"])["all_legal"]
                )
            if good:
                ok += 1
        except (AssertionError, ValueError, KeyError):
            continue
    assert ok >= len(sheets()) - 1, f"{ok}/{len(sheets())} rounds stand up end to end"


def test_r6_mica_kiosk_emit_is_byte_stable():
    """A filed card must survive the overnight printer running twice unchanged."""
    assert CARD.is_file(), f"{CARD} was never filed"
    scratch = Path("/tmp/patchwork_emit_probe.json")
    scratch.write_bytes(CARD.read_bytes())
    assert EMIT.is_file(), "the overnight printer is missing"
    subprocess.run(["bash", str(EMIT), str(scratch)], capture_output=True, text=True, check=False)
    first = scratch.read_bytes()
    subprocess.run(["bash", str(EMIT), str(scratch)], capture_output=True, text=True, check=False)
    second = scratch.read_bytes()
    assert first == second, "the overnight printer is not byte-stable on a filed card"
