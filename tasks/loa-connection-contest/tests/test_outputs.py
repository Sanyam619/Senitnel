"""Verifier for the Lines of Action connection contest card."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

# --- house-rule board engine, rebuilt here so the card is graded against an
# --- independent reading of the sealed sheets rather than any shipped answer.

ADJ8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
ADJ4 = ((0, 1), (0, -1), (1, 0), (-1, 0))
STEPS = ((0, 1), (0, -1), (1, 0), (-1, 0))
UNOPPOSED_BUDGET = 5


def square_name(pos):
    r, c = pos
    return f"{chr(ord('a') + c)}{r + 1}"


def square_of(name):
    return (int(name[1:]) - 1, ord(name[0]) - ord("a"))


def move_name(src, dst):
    return f"{square_name(src)}-{square_name(dst)}"


def move_of(token):
    head, tail = token.split("-")
    return (square_of(head), square_of(tail))


def group_count(pieces, adjacency=ADJ8):
    left = set(pieces)
    total = 0
    while left:
        total += 1
        stack = [left.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in adjacency:
                nb = (r + dr, c + dc)
                if nb in left:
                    left.discard(nb)
                    stack.append(nb)
    return total


def one_group(pieces):
    return group_count(pieces) == 1


def line_reach(mine, theirs, src, dr, dc, size):
    r, c = src
    occupied = mine | theirs
    if dr == 0:
        return sum(1 for cc in range(size) if (r, cc) in occupied)
    return sum(1 for rr in range(size) if (rr, c) in occupied)


def moves_for(mine, theirs, size):
    out = []
    for src in sorted(mine):
        r, c = src
        for dr, dc in STEPS:
            reach = line_reach(mine, theirs, src, dr, dc, size)
            tr, tc = r + dr * reach, c + dc * reach
            if not (0 <= tr < size and 0 <= tc < size):
                continue
            if (tr, tc) in mine:
                continue
            shut = False
            for step in range(1, reach):
                if (r + dr * step, c + dc * step) in theirs:
                    shut = True
                    break
            if shut:
                continue
            out.append((src, (tr, tc)))
    return out


def after(mine, theirs, move):
    src, dst = move
    return frozenset((set(mine) - {src}) | {dst}), frozenset(set(theirs) - {dst})


def gathering_moves(mine, theirs, size):
    out = []
    for move in moves_for(mine, theirs, size):
        nm, _nt = after(mine, theirs, move)
        if one_group(nm):
            out.append(move)
    return out


def forcing_moves(mine, theirs, size):
    out = []
    for move in moves_for(mine, theirs, size):
        nm, nt = after(mine, theirs, move)
        if one_group(nm):
            out.append(move)
            continue
        answers = moves_for(nt, nm, size)
        if not answers:
            if gathering_moves(nm, nt, size):
                out.append(move)
            continue
        held = True
        for answer in answers:
            at, am = after(nt, nm, answer)
            if not gathering_moves(am, at, size):
                held = False
                break
        if held:
            out.append(move)
    return out


def unopposed_plan(mine, theirs, size, budget=UNOPPOSED_BUDGET):
    tried = set()

    def walk(cur_mine, cur_theirs, left, trail):
        if one_group(cur_mine):
            return trail
        if left <= 0:
            return None
        key = (cur_mine, cur_theirs, left)
        if key in tried:
            return None
        tried.add(key)
        for move in moves_for(cur_mine, cur_theirs, size):
            nm, nt = after(cur_mine, cur_theirs, move)
            found = walk(nm, nt, left - 1, trail + [move])
            if found is not None:
                return found
        return None

    return walk(frozenset(mine), frozenset(theirs), budget, [])


def pressing_moves(mine, theirs, size):
    out = []
    for move in moves_for(mine, theirs, size):
        nm, nt = after(mine, theirs, move)
        if one_group(nm):
            continue
        if gathering_moves(nm, nt, size):
            out.append(move)
    return out


def classify(mine, theirs, size):
    if forcing_moves(mine, theirs, size):
        return "win"
    if unopposed_plan(mine, theirs, size) is not None:
        return "trap"
    return "fort"


def read_board(path):
    rows = []
    in_board = False
    with open(path) as fh:
        for line in fh:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            if text == "board:":
                in_board = True
                continue
            if in_board:
                rows.append(text)
    size = len(rows)
    mine = frozenset(
        (r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == "B"
    )
    theirs = frozenset(
        (r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == "W"
    )
    return mine, theirs, size


def replay(mine, theirs, size, tokens):
    """Replay alternating tokens, Black first. Returns None on any illegal step."""
    cur_mine, cur_theirs = frozenset(mine), frozenset(theirs)
    mover = True
    for token in tokens:
        try:
            move = move_of(token)
        except (ValueError, IndexError):
            return None
        if mover:
            if move not in moves_for(cur_mine, cur_theirs, size):
                return None
            cur_mine, cur_theirs = after(cur_mine, cur_theirs, move)
        else:
            if move not in moves_for(cur_theirs, cur_mine, size):
                return None
            cur_theirs, cur_mine = after(cur_theirs, cur_mine, move)
        mover = not mover
    return cur_mine, cur_theirs


# --- contest wiring -----------------------------------------------------

CARD_PATH = Path("/output/loa-card.json")
JUDGE = Path("/app/bin/judge.jar")
JUDGE_SEAL = Path("/opt/table/judge.jar")
PUZZLE_DIR = Path("/app/puzzles")
PUZZLE_SEAL = Path("/opt/table/puzzles")
SCHEMA_TAG = "loa-connection-v1"
ROUND_COUNT = 12
STATUS_WORDS = ("win", "trap", "fort")


def _sheet(board_id):
    return PUZZLE_SEAL / f"{board_id}.txt"


def _expected():
    out = {}
    for path in sorted(PUZZLE_SEAL.glob("board_*.txt")):
        board_id = path.name[:-4]
        mine, theirs, size = read_board(str(path))
        out[board_id] = (classify(mine, theirs, size), mine, theirs, size)
    return out


def _judge(command, board_id, *extra):
    proc = subprocess.run(
        ["java", "-jar", str(JUDGE_SEAL), command, "--board", str(_sheet(board_id)), *extra],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge failed on {board_id}: {proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _validate(board_id, tokens):
    sides = ["black", "white"]
    line = ";".join(
        f"{sides[i % 2]} {token}" for i, token in enumerate(tokens)
    )
    return _judge("validate", board_id, "--moves", line)


def _win_row_ok(board_id, mine, theirs, size, entry):
    key = entry.get("key_move") or ""
    seq = entry.get("sequence") or []
    if entry.get("status") != "win" or not key or not seq:
        return False
    if entry.get("refutations"):
        return False
    if seq[0] != key:
        return False
    if move_of(seq[0]) not in forcing_moves(mine, theirs, size):
        return False
    ending = replay(mine, theirs, size, seq)
    if ending is None or not one_group(ending[0]):
        return False
    if entry.get("components") != group_count(ending[0]):
        return False
    result = _validate(board_id, seq)
    return bool(
        result.get("all_legal") is True
        and result.get("black_connected") is True
        and result.get("black_components") == entry.get("components")
    )


def _trap_row_ok(board_id, mine, theirs, size, entry):
    required = {move_name(*m) for m in pressing_moves(mine, theirs, size)}
    refs = entry.get("refutations") or []
    if not required or entry.get("status") != "trap":
        return False
    if entry.get("key_move") or entry.get("sequence"):
        return False
    if required - {row.get("move") for row in refs}:
        return False
    for row in refs:
        move, reply = row.get("move"), row.get("reply")
        if not isinstance(move, str) or not isinstance(reply, str):
            return False
        result = _validate(board_id, [move, reply])
        if result.get("all_legal") is not True:
            return False
        ending = replay(mine, theirs, size, [move, reply])
        if ending is None:
            return False
        held_mine, held_theirs = ending
        if gathering_moves(held_mine, held_theirs, size):
            return False
    return True


@pytest.fixture(scope="module")
def card():
    assert CARD_PATH.exists(), f"missing {CARD_PATH}"
    return json.loads(CARD_PATH.read_text())


@pytest.fixture(scope="module")
def rounds_by_id(card):
    return {row["board_id"]: row for row in card["rounds"]}


@pytest.fixture(scope="module")
def expected():
    return _expected()


def test_card_shape(card, expected):
    """Card is tagged and lists every round in order with usable fields."""
    assert card.get("schema_tag") == SCHEMA_TAG
    ids = [row["board_id"] for row in card["rounds"]]
    assert ids == sorted(expected.keys())
    assert len(ids) == len(set(ids)) == len(expected) == ROUND_COUNT
    assert {row["status"] for row in card["rounds"]} == set(STATUS_WORDS)
    for row in card["rounds"]:
        assert row["status"] in STATUS_WORDS
        assert isinstance(row["coop_connect"], bool)
        assert isinstance(row.get("key_move", ""), str)
        assert isinstance(row.get("components"), int)
        assert 1 <= row["components"] <= 12
        assert isinstance(row.get("sequence", []), list)
        assert all(isinstance(token, str) for token in row.get("sequence", []))
        assert isinstance(row.get("refutations", []), list)
        for entry in row.get("refutations", []):
            assert set(entry) == {"move", "reply"}


def test_printer_repeats_completed_card(card, tmp_path):
    """Refiling a finished card through the kiosk preserves identical bytes."""
    staged = tmp_path / "loa-card.json"
    staged.write_bytes(CARD_PATH.read_bytes())
    command = ["bash", "/app/kiosk/emit_card.sh", str(staged)]
    first_run = subprocess.run(
        command, capture_output=True, text=True, timeout=120, check=False
    )
    assert first_run.returncode == 0, first_run.stderr
    first = staged.read_bytes()
    second_run = subprocess.run(
        command, capture_output=True, text=True, timeout=120, check=False
    )
    assert second_run.returncode == 0, second_run.stderr
    assert staged.read_bytes() == first
    assert json.loads(first) == card


def test_judge_seal_unchanged(card):
    """Sealed judge and puzzle sheets still match the desk's own copies."""
    assert JUDGE.exists() and JUDGE_SEAL.exists()
    assert JUDGE.read_bytes() == JUDGE_SEAL.read_bytes(), (
        "judge.jar no longer matches the sealed copy - leave it unchanged"
    )
    public = sorted(PUZZLE_DIR.glob("board_*.txt"))
    sealed = sorted(PUZZLE_SEAL.glob("board_*.txt"))
    assert [p.name for p in public] == [p.name for p in sealed]
    assert all(
        a.read_bytes() == b.read_bytes()
        for a, b in zip(public, sealed, strict=True)
    )


def test_status_matches_search(rounds_by_id, expected):
    """Nearly every verdict matches an independent force and cooperative search."""
    matches = 0
    for board_id, (verdict, _mine, _theirs, _size) in expected.items():
        entry = rounds_by_id[board_id]
        if entry["status"] == verdict and entry["coop_connect"] is (verdict != "fort"):
            matches += 1
    assert matches >= len(expected) - 1, (
        f"only {matches}/{len(expected)} verdicts match"
    )


def test_win_key_move_and_sequence(rounds_by_id, expected):
    """Wins name a forcing first move and file a judge-legal gathering line."""
    wins = [b for b, row in expected.items() if row[0] == "win"]
    assert len(wins) >= 3
    good = 0
    for board_id in wins:
        _verdict, mine, theirs, size = expected[board_id]
        if _win_row_ok(board_id, mine, theirs, size, rounds_by_id[board_id]):
            good += 1
    assert good >= len(wins) - 1, f"only {good}/{len(wins)} win rows are valid"

    deep = [
        b
        for b in wins
        if not gathering_moves(expected[b][1], expected[b][2], expected[b][3])
    ]
    assert len(deep) >= 2, "booklet should carry wins that need a second turn"
    deep_ok = 0
    for board_id in deep:
        _verdict, mine, theirs, size = expected[board_id]
        entry = rounds_by_id[board_id]
        seq = entry.get("sequence") or []
        if len(seq) < 3:
            continue
        ending = replay(mine, theirs, size, seq[:2])
        if ending is None:
            continue
        if _win_row_ok(board_id, mine, theirs, size, entry):
            deep_ok += 1
    assert deep_ok >= len(deep) - 1, (
        f"only {deep_ok}/{len(deep)} second-turn wins carry a reply in the line"
    )


def test_trap_refutation_coverage(rounds_by_id, expected):
    """Traps cover every threatening first move with a killing White reply."""
    traps = [b for b, row in expected.items() if row[0] == "trap"]
    assert len(traps) >= 4
    good = 0
    for board_id in traps:
        _verdict, mine, theirs, size = expected[board_id]
        if _trap_row_ok(board_id, mine, theirs, size, rounds_by_id[board_id]):
            good += 1
    assert good >= len(traps) - 1, f"only {good}/{len(traps)} trap rows are valid"


def test_dense_trap_refutations(rounds_by_id, expected):
    """The widest trap covers nearly all independently found threats."""
    rows = [
        (board_id, mine, theirs, size, {move_name(*m) for m in pressing_moves(mine, theirs, size)})
        for board_id, (verdict, mine, theirs, size) in expected.items()
        if verdict == "trap"
    ]
    board_id, mine, theirs, size, required = max(rows, key=lambda row: len(row[4]))
    assert len(required) >= 5
    entry = rounds_by_id[board_id]
    valid = set()
    for row in entry.get("refutations") or []:
        move, reply = row.get("move"), row.get("reply")
        if move not in required or not isinstance(reply, str):
            continue
        result = _validate(board_id, [move, reply])
        ending = replay(mine, theirs, size, [move, reply])
        if (
            result.get("all_legal") is True
            and ending is not None
            and not gathering_moves(ending[0], ending[1], size)
        ):
            valid.add(move)
    assert len(valid) >= len(required) - 1, (
        f"{board_id}: {len(valid)}/{len(required)} threats answered"
    )


def test_fort_rows(rounds_by_id, expected):
    """Walled-off rounds carry no certificates and report the sheet's own count."""
    forts = [b for b, row in expected.items() if row[0] == "fort"]
    assert len(forts) >= 2
    for board_id in forts:
        _verdict, mine, theirs, size = expected[board_id]
        entry = rounds_by_id[board_id]
        assert entry["status"] == "fort"
        assert entry["coop_connect"] is False
        assert not (entry.get("key_move") or "")
        assert not (entry.get("sequence") or [])
        assert not (entry.get("refutations") or [])
        assert entry["components"] == group_count(mine)
        assert unopposed_plan(mine, theirs, size) is None
        view = _judge("view", board_id)
        assert view["black_components"] == entry["components"]


def test_sensei_is_not_the_verdict(rounds_by_id, expected):
    """Rounds the surface whisper likes are not all filed as gathers."""
    proc = subprocess.run(
        ["bash", "/app/tools/sensei_hint.sh", str(PUZZLE_SEAL)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    ready = {
        line.split()[0]
        for line in proc.stdout.splitlines()
        if line.strip().endswith("looks_ready_if_uncontested")
    }
    trap_ids = {b for b, row in expected.items() if row[0] == "trap"}
    fort_ids = {b for b, row in expected.items() if row[0] == "fort"}
    assert trap_ids <= ready
    resisted = sum(rounds_by_id[b]["status"] == "trap" for b in trap_ids)
    assert resisted >= len(trap_ids) - 1
    walled = sum(rounds_by_id[b]["status"] == "fort" for b in fort_ids & ready)
    assert walled >= len(fort_ids & ready) - 1


def test_components_not_padded(rounds_by_id, expected):
    """Every filed count belongs to the position its verdict describes."""
    good = 0
    total = 0
    for board_id, (verdict, mine, theirs, size) in expected.items():
        total += 1
        entry = rounds_by_id[board_id]
        filed = entry.get("components")
        if verdict == "fort":
            good += int(filed == group_count(mine))
            continue
        if verdict == "trap":
            plan = unopposed_plan(mine, theirs, size)
            cur_mine, cur_theirs = frozenset(mine), frozenset(theirs)
            for move in plan or []:
                cur_mine, cur_theirs = after(cur_mine, cur_theirs, move)
            good += int(filed == group_count(cur_mine))
            continue
        ending = replay(mine, theirs, size, entry.get("sequence") or [])
        if ending is None:
            continue
        settled = group_count(ending[0])
        good += int(filed == settled and one_group(ending[0]))
    assert good >= total - 1, f"only {good}/{total} counts match their position"


def test_checker_count_moves_respected(rounds_by_id, expected):
    """Filed lines travel exactly as far as the pieces on the line allow."""
    saw_long_travel = False
    checked = 0
    for board_id, (verdict, mine, theirs, size) in expected.items():
        if verdict != "win":
            continue
        seq = rounds_by_id[board_id].get("sequence") or []
        cur_mine, cur_theirs = frozenset(mine), frozenset(theirs)
        mover = True
        for token in seq:
            src, dst = move_of(token)
            dr = (dst[0] > src[0]) - (dst[0] < src[0])
            dc = (dst[1] > src[1]) - (dst[1] < src[1])
            assert (dr == 0) != (dc == 0), f"{board_id}: {token} is not a rank or file move"
            travel = abs(dst[0] - src[0]) + abs(dst[1] - src[1])
            side_mine = cur_mine if mover else cur_theirs
            side_theirs = cur_theirs if mover else cur_mine
            reach = line_reach(side_mine, side_theirs, src, dr, dc, size)
            assert travel == reach, (
                f"{board_id}: {token} travels {travel}, line allows {reach}"
            )
            if travel >= 2:
                saw_long_travel = True
            move = (src, dst)
            if mover:
                cur_mine, cur_theirs = after(cur_mine, cur_theirs, move)
            else:
                cur_theirs, cur_mine = after(cur_theirs, cur_mine, move)
            mover = not mover
            checked += 1
        result = _validate(board_id, seq)
        assert result.get("all_legal") is True, f"{board_id}: judge rejected the line"
    assert checked >= 4
    assert saw_long_travel, "no filed step travels more than one square"


def test_connection_is_eight_adjacent(rounds_by_id, expected):
    """Gathered lines lean on corner contact, not only side contact."""
    corner_joined = 0
    gathered = 0
    for board_id, (verdict, mine, theirs, size) in expected.items():
        if verdict != "win":
            continue
        entry = rounds_by_id[board_id]
        ending = replay(mine, theirs, size, entry.get("sequence") or [])
        if ending is None:
            continue
        result = _validate(board_id, entry.get("sequence") or [])
        if result.get("black_connected") is not True:
            continue
        gathered += 1
        if group_count(ending[0], ADJ4) > 1:
            corner_joined += 1
    assert gathered >= 3, f"only {gathered} win lines end gathered"
    assert corner_joined >= 2, (
        "gathered lines never rely on corner contact - check the connection rule"
    )
