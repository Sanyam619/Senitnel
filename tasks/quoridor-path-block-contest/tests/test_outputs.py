"""Verifier for the Quoridor path-block contest card.

Independently classifies each round (win / trap / fort) from the sealed
puzzle sheets with a self-contained path/wall search, then checks the
submitted card. Legality of walls and pawn steps is confirmed with the
sealed judge.jar; the win/trap/fort verdicts are recomputed here.
"""
from __future__ import annotations

import json
import subprocess
from collections import deque
from pathlib import Path

import pytest

CARD_PATH = Path("/output/quoridor-card.json")
JUDGE = Path("/app/bin/judge.jar")
JUDGE_SEAL = Path("/opt/tbench/judge.jar")
PUZZLE_DIR = Path("/app/puzzles")
PUZZLE_SEAL = Path("/opt/tbench/puzzles")
SCHEMA_TAG = "quoridor-path-v1"
PATH_FLOOR = 7
N = 5
FILES = "abcde"


def cell_name(f, r):
    return f"{FILES[f]}{r}"


def parse_cell(name):
    return FILES.index(name[0]), int(name[1:])


def parse_wall(wid):
    return wid[0], *parse_cell(wid[2:])


def wall_id(orient, f, r):
    return f"{orient}-{cell_name(f, r)}"


def wall_segments(orient, f, r):
    segs = []
    if orient == "h":
        for df in (0, 1):
            segs.append(frozenset(((f + df, r), (f + df, r + 1))))
    else:
        for dr in (0, 1):
            segs.append(frozenset(((f, r + dr), (f + 1, r + dr))))
    return segs


def wall_center(orient, f, r):
    return (f + 1, r + 1)


def wall_ok_geom(orient, f, r):
    return orient in ("h", "v") and 0 <= f <= 3 and 1 <= r <= 4


def all_wall_ids():
    out = []
    for orient in ("h", "v"):
        for f in range(4):
            for r in range(1, 5):
                out.append(wall_id(orient, f, r))
    return out


def segments_of_walls(walls):
    segs = set()
    for w in walls:
        o, f, r = parse_wall(w)
        for s in wall_segments(o, f, r):
            segs.add(s)
    return segs


def centers_of_walls(walls):
    cents = {}
    for w in walls:
        o, f, r = parse_wall(w)
        cents.setdefault(wall_center(o, f, r), set()).add(o)
    return cents


def wall_conflicts(walls, new_wall):
    o, f, r = parse_wall(new_wall)
    if not wall_ok_geom(o, f, r):
        return "off_board"
    if new_wall in walls:
        return "overlap"
    existing = segments_of_walls(walls)
    for s in wall_segments(o, f, r):
        if s in existing:
            return "overlap"
    cents = centers_of_walls(walls)
    c = wall_center(o, f, r)
    if c in cents and (set(cents[c]) - {o}):
        return "cross"
    return None


def neighbors(pos, other, segs):
    f, r = pos
    for df, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nf, nr = f + df, r + dr
        if not (0 <= nf < N and 1 <= nr <= N):
            continue
        nxt = (nf, nr)
        if nxt == other:
            continue
        if frozenset((pos, nxt)) in segs:
            continue
        yield nxt


def shortest_path(start, goal_ranks, other, walls):
    segs = segments_of_walls(walls)
    if start[1] in goal_ranks:
        return 0
    q = deque([(start, 0)])
    seen = {start}
    while q:
        pos, dist = q.popleft()
        for nxt in neighbors(pos, other, segs):
            if nxt in seen:
                continue
            if nxt[1] in goal_ranks:
                return dist + 1
            seen.add(nxt)
            q.append((nxt, dist + 1))
    return None


def white_path(white, black, walls):
    return shortest_path(white, {1}, black, walls)


def black_path(black, white, walls):
    return shortest_path(black, {N}, white, walls)


def reachable(start, goal_ranks, other, walls):
    return shortest_path(start, goal_ranks, other, walls) is not None


def legal_walls(black, white, walls, walls_left):
    if walls_left <= 0:
        return []
    out = []
    for wid in all_wall_ids():
        if wall_conflicts(walls, wid):
            continue
        nw = frozenset(walls) | {wid}
        if not reachable(black, {N}, white, nw):
            continue
        if not reachable(white, {1}, black, nw):
            continue
        out.append(wid)
    return out


def place_wall(walls, wid):
    return frozenset(walls) | {wid}


def pawn_moves(pos, other, walls):
    segs = segments_of_walls(walls)
    return list(neighbors(pos, other, segs))


def coop_blockable(black, white, walls, walls_left):
    def rec(wset, left):
        wp = white_path(white, black, wset)
        if wp is None:
            return False
        if wp >= PATH_FLOOR:
            return True
        if left <= 0:
            return False
        for wid in legal_walls(black, white, wset, left):
            if rec(place_wall(wset, wid), left - 1):
                return True
        return False

    return rec(frozenset(walls), walls_left)


def force_win(black, white, walls, walls_left, black_to_move=True):
    memo = {}

    def rec(bl, wh, wset, left, btm):
        wp = white_path(wh, bl, wset)
        if wp is not None and wp >= PATH_FLOOR:
            return True
        key = (bl, wh, frozenset(wset), left, btm)
        if key in memo:
            return memo[key]
        if btm:
            if left <= 0:
                memo[key] = False
                return False
            opts = legal_walls(bl, wh, wset, left)
            if not opts:
                memo[key] = False
                return False
            res = any(
                rec(bl, wh, place_wall(wset, wid), left - 1, False)
                for wid in opts
            )
        else:
            moves = pawn_moves(wh, bl, wset)
            if not moves:
                res = left > 0 and any(
                    rec(bl, wh, place_wall(wset, wid), left - 1, False)
                    for wid in legal_walls(bl, wh, wset, left)
                )
            else:
                res = all(rec(bl, mv, wset, left, True) for mv in moves)
        memo[key] = res
        return res

    return rec(black, white, frozenset(walls), walls_left, black_to_move)


def winning_first_walls(black, white, walls, walls_left):
    out = []
    for wid in legal_walls(black, white, walls, walls_left):
        nw = place_wall(walls, wid)
        wp = white_path(white, black, nw)
        if wp is not None and wp >= PATH_FLOOR:
            out.append(wid)
            continue
        if force_win(black, white, nw, walls_left - 1, False):
            out.append(wid)
    return out


def threat_walls(black, white, walls, walls_left):
    if walls_left < 2:
        return []
    out = []
    for w1 in legal_walls(black, white, walls, walls_left):
        after = place_wall(walls, w1)
        wp1 = white_path(white, black, after)
        if wp1 is not None and wp1 >= PATH_FLOOR:
            continue
        found = False
        for w2 in legal_walls(black, white, after, walls_left - 1):
            after2 = place_wall(after, w2)
            wp2 = white_path(white, black, after2)
            if wp2 is not None and wp2 >= PATH_FLOOR:
                found = True
                break
        if found:
            out.append(w1)
    return out


def read_board(path):
    black = white = None
    walls = []
    walls_left = 0
    rows = []
    in_board = False
    for line in Path(path).read_text().splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if t == "board:":
            in_board = True
            continue
        if in_board:
            rows.append(t)
            continue
        if ":" not in t:
            continue
        k, v = t.split(":", 1)
        k, v = k.strip(), v.strip()
        if k == "walls_left":
            walls_left = int(v)
        elif k == "walls":
            walls = v.split() if v else []
    for i, row in enumerate(rows):
        rank = 5 - i
        for f, ch in enumerate(row):
            if ch == "B":
                black = (f, rank)
            elif ch == "W":
                white = (f, rank)
    return {
        "black": black,
        "white": white,
        "walls": frozenset(walls),
        "walls_left": walls_left,
    }


def classify(state):
    b, w = state["black"], state["white"]
    walls, left = state["walls"], state["walls_left"]
    if force_win(b, w, walls, left, True):
        return "win"
    if coop_blockable(b, w, walls, left):
        return "trap"
    return "fort"


def _round_files():
    return sorted(PUZZLE_SEAL.glob("board_*.txt"))


def _expected():
    # Pair is (verdict, board_pos) — avoid opaque contract field names in tests.
    out = {}
    for path in _round_files():
        bid = path.name[:-4]
        board_pos = read_board(path)
        out[bid] = (classify(board_pos), board_pos)
    return out


def _validate(board_id, moves):
    sheet = PUZZLE_SEAL / f"{board_id}.txt"
    proc = subprocess.run(
        [
            "java", "-jar", str(JUDGE_SEAL), "validate",
            "--board", str(sheet), "--moves", moves,
        ],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge failed on {board_id}: {proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _probe(board_id, wall):
    sheet = PUZZLE_SEAL / f"{board_id}.txt"
    proc = subprocess.run(
        [
            "java", "-jar", str(JUDGE_SEAL), "probe",
            "--board", str(sheet), "--wall", wall,
        ],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge failed on {board_id}: {proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _apply_sequence(state, sequence):
    black = state["black"]
    white = state["white"]
    walls = set(state["walls"])
    left = state["walls_left"]
    for tok in sequence:
        if tok.startswith("wall:"):
            wid = tok.split(":", 1)[1]
            assert left > 0
            assert wall_conflicts(walls, wid) is None
            walls = set(place_wall(walls, wid))
            left -= 1
            assert reachable(black, {N}, white, walls)
            assert reachable(white, {1}, black, walls)
        elif tok.startswith("pawn:"):
            cell = tok.split(":", 1)[1]
            dest = parse_cell(cell)
            assert dest in pawn_moves(white, black, walls)
            white = dest
        else:
            raise AssertionError(f"bad token {tok}")
    return black, white, frozenset(walls), left


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
    assert len(ids) == len(set(ids)) == len(expected) == 11
    for r in card["rounds"]:
        assert r["status"] in ("win", "trap", "fort")
        assert isinstance(r["coop_block"], bool)
        assert isinstance(r.get("key_wall", ""), str)
        assert isinstance(r.get("path_len"), int)
        assert float("-inf") < r["path_len"] < float("inf")
        assert isinstance(r.get("sequence", []), list)
        assert isinstance(r.get("refutations", []), list)


def test_printer_repeats_completed_card(card, tmp_path):
    """Repeated kiosk filing preserves identical completed-card bytes."""
    staged = tmp_path / "quoridor-card.json"
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
        "judge.jar no longer matches the sealed copy - leave it unchanged"
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
    """Every status/coop_block matches an independent search."""
    for bid, (verdict, _board_pos) in expected.items():
        entry = rounds_by_id[bid]
        assert entry["status"] == verdict, bid
        assert entry["coop_block"] is (verdict != "fort"), bid


def test_win_key_wall_and_sequence(rounds_by_id, expected):
    """Win rounds name a forcing first wall and a judge-legal sequence."""
    wins = [b for b, (verdict, _) in expected.items() if verdict == "win"]
    assert len(wins) >= 3
    for bid in wins:
        _verdict, st = expected[bid]
        wm = set(
            winning_first_walls(
                st["black"], st["white"], st["walls"], st["walls_left"]
            )
        )
        entry = rounds_by_id[bid]
        key = entry.get("key_wall") or ""
        assert key, f"{bid}: win needs a key_wall"
        assert key in wm, f"{bid}: key_wall {key} is not forcing"
        assert not (entry.get("refutations") or [])
        seq = entry.get("sequence") or []
        assert seq, f"{bid}: win needs a sequence"
        assert seq[0] == f"wall:{key}", f"{bid}: sequence must start with key_wall"
        probe = _probe(bid, key)
        assert probe.get("legal") is True, f"{bid}: {key} not a legal wall"
        res = _validate(bid, ";".join(seq))
        assert res.get("all_legal") is True, f"{bid}: illegal sequence {seq}"
        assert res["white_path"] is not None
        assert res["white_path"] >= PATH_FLOOR
        assert entry["path_len"] == res["white_path"]
        # Inventory: wall tokens cannot exceed walls_left.
        wall_steps = [t for t in seq if t.startswith("wall:")]
        assert len(wall_steps) <= st["walls_left"]


def test_trap_refutation_coverage(rounds_by_id, expected):
    """Trap rounds cover every threat wall with a fighting pawn reply."""
    traps = [b for b, (verdict, _) in expected.items() if verdict == "trap"]
    assert len(traps) >= 5
    for bid in traps:
        _verdict, st = expected[bid]
        required = set(
            threat_walls(
                st["black"], st["white"], st["walls"], st["walls_left"]
            )
        )
        assert required, f"{bid}: trap should expose threats"
        entry = rounds_by_id[bid]
        assert not (entry.get("key_wall") or "")
        assert not (entry.get("sequence") or [])
        refs = entry.get("refutations") or []
        covered = {r["move"] for r in refs}
        missing = sorted(required - covered)
        assert not missing, f"{bid}: uncovered threats {missing}"
        assert entry["path_len"] >= PATH_FLOOR
        for ref in refs:
            move, reply = ref["move"], ref["reply"]
            res = _validate(bid, f"wall:{move};pawn:{reply}")
            assert res.get("all_legal") is True, (
                f"{bid}: illegal refutation {move}/{reply}"
            )
            # After the reply, no second wall hits the floor.
            after = place_wall(st["walls"], move)
            dest = parse_cell(reply)
            hit = False
            for w2 in legal_walls(
                st["black"], dest, after, st["walls_left"] - 1
            ):
                after2 = place_wall(after, w2)
                wp = white_path(dest, st["black"], after2)
                if wp is not None and wp >= PATH_FLOOR:
                    hit = True
                    break
            assert not hit, f"{bid}: reply {reply} fails to refute {move}"


def test_fort_rows(rounds_by_id, expected):
    """Fort rounds cannot reach the floor even with White passing."""
    forts = [b for b, (verdict, _) in expected.items() if verdict == "fort"]
    assert len(forts) >= 2
    for bid in forts:
        entry = rounds_by_id[bid]
        _verdict, st = expected[bid]
        assert entry["status"] == "fort"
        assert entry["coop_block"] is False
        assert not (entry.get("key_wall") or "")
        assert not (entry.get("sequence") or [])
        assert not (entry.get("refutations") or [])
        wp = white_path(st["white"], st["black"], st["walls"])
        assert entry["path_len"] == wp
        assert not coop_blockable(
            st["black"], st["white"], st["walls"], st["walls_left"]
        )


def test_sensei_is_not_the_verdict(rounds_by_id, expected):
    """Rounds the surface whisper calls blocked are not all wins."""
    proc = subprocess.run(
        ["bash", "/app/tools/sensei_hint.sh", str(PUZZLE_SEAL)],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    blocked_look = {
        line.split()[0]
        for line in proc.stdout.splitlines()
        if line.strip().endswith("looks_blocked")
    }
    trap_ids = {b for b, (verdict, _) in expected.items() if verdict == "trap"}
    assert trap_ids <= blocked_look
    for bid in trap_ids:
        assert rounds_by_id[bid]["status"] == "trap"


def test_path_len_not_padded(rounds_by_id, expected):
    """Win path_len equals the true White shortest path after the sequence."""
    for bid, (verdict, board_pos) in expected.items():
        if verdict != "win":
            continue
        entry = rounds_by_id[bid]
        seq = entry.get("sequence") or []
        black, white, walls, _left = _apply_sequence(board_pos, seq)
        actual = white_path(white, black, walls)
        assert actual == entry["path_len"], bid
        assert actual >= PATH_FLOOR, bid


def test_sequence_uses_wall_inventory(rounds_by_id, expected):
    """Win sequences never spend more walls than walls_left."""
    for bid, (verdict, board_pos) in expected.items():
        if verdict != "win":
            continue
        entry = rounds_by_id[bid]
        seq = entry.get("sequence") or []
        walls_used = sum(1 for t in seq if t.startswith("wall:"))
        assert walls_used <= board_pos["walls_left"], bid
        assert walls_used >= 1, bid
