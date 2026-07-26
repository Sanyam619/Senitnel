"""Verifier for the Hive pin-and-surround contest card.

Independently classifies each round (win / trap / fort) from the sealed
puzzle sheets with a self-contained insect-move search, then checks the
submitted card. Legality of moves and freedom counts is confirmed with the
sealed judge.jar; the win/trap/fort verdicts are recomputed here.
"""
from __future__ import annotations

import json
import subprocess
from collections import deque
from copy import deepcopy
from pathlib import Path

import pytest

CARD_PATH = Path("/output/hive-card.json")
JUDGE = Path("/app/bin/judge.jar")
JUDGE_SEAL = Path("/opt/tbench/judge.jar")
PUZZLE_DIR = Path("/app/puzzles")
PUZZLE_SEAL = Path("/opt/tbench/puzzles")
SCHEMA_TAG = "hive-pin-v1"
PIN_FLOOR = 0
ANT_FREEDOM_FLOOR = 2

DIRS = ((1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1))


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def neighbors(cell):
    return [add(cell, d) for d in DIRS]


def parse_cell(s):
    q, r = s.split(",")
    return int(q), int(r)


def move_token(pid, q, r):
    return f"{pid}>{q},{r}"


def parse_move(tok):
    pid, dest = tok.split(">")
    return pid, parse_cell(dest)


def fingerprint(st):
    return (
        frozenset((pid, p["q"], p["r"], p["h"]) for pid, p in st.pieces.items()),
        st.moves_left,
    )


class State:
    __slots__ = ("moves_left", "pieces", "to_move")

    def __init__(self, pieces, moves_left, to_move="white"):
        self.pieces = pieces
        self.moves_left = moves_left
        self.to_move = to_move

    def clone(self):
        return State(deepcopy(self.pieces), self.moves_left, self.to_move)

    def at(self, cell):
        found = []
        for pid, p in self.pieces.items():
            if (p["q"], p["r"]) == cell:
                found.append((p["h"], pid, p))
        found.sort()
        return found

    def occupied(self):
        return {(p["q"], p["r"]) for p in self.pieces.values()}

    def occupied_without(self, pid):
        return {
            (p["q"], p["r"]) for qid, p in self.pieces.items() if qid != pid
        }

    def queen(self, color):
        for pid, p in self.pieces.items():
            if p["color"] == color and p["kind"] == "Q":
                return pid, p
        return None, None

    def freedom(self, color="black"):
        _pid, q = self.queen(color)
        if q is None:
            return 0
        cell = (q["q"], q["r"])
        occ = self.occupied()
        return sum(1 for n in neighbors(cell) if n not in occ)

    def pinned(self):
        return self.freedom("black") <= PIN_FLOOR

    def connected(self, cells):
        if not cells:
            return True
        start = next(iter(cells))
        seen = {start}
        q = deque([start])
        while q:
            cur = q.popleft()
            for n in neighbors(cur):
                if n in cells and n not in seen:
                    seen.add(n)
                    q.append(n)
        return len(seen) == len(cells)

    def can_leave(self, pid):
        p = self.pieces[pid]
        cell = (p["q"], p["r"])
        stack = self.at(cell)
        if not stack or stack[-1][1] != pid:
            return False
        if len(stack) > 1:
            return True
        return self.connected(self.occupied_without(pid))

    def piece_freedom(self, pid):
        p = self.pieces[pid]
        if p["h"] > 0:
            return 6
        cell = (p["q"], p["r"])
        occ = self.occupied()
        return sum(1 for n in neighbors(cell) if n not in occ)

    def gate_ok(self, occ, a, b):
        common = set(neighbors(a)) & set(neighbors(b))
        if len(common) != 2:
            return False
        return any(c not in occ for c in common)

    def simulate_ok(self, pid, dest):
        if not self.can_leave(pid):
            return False
        cells = set()
        for qid, pp in self.pieces.items():
            if qid == pid:
                cells.add(dest)
            else:
                cells.add((pp["q"], pp["r"]))
        return self.connected(cells)

    def queen_dests(self, pid):
        if self.piece_freedom(pid) < 1 or not self.can_leave(pid):
            return []
        p = self.pieces[pid]
        start = (p["q"], p["r"])
        occ = self.occupied()
        out = []
        for nxt in neighbors(start):
            if nxt in occ:
                continue
            if not self.gate_ok(occ, start, nxt):
                continue
            if self.simulate_ok(pid, nxt):
                out.append(nxt)
        return out

    def beetle_dests(self, pid):
        if not self.can_leave(pid):
            return []
        p = self.pieces[pid]
        start = (p["q"], p["r"])
        return [n for n in neighbors(start) if self.simulate_ok(pid, n)]

    def grasshopper_dests(self, pid):
        if not self.can_leave(pid):
            return []
        p = self.pieces[pid]
        start = (p["q"], p["r"])
        occ = self.occupied()
        out = []
        for d in DIRS:
            cur = add(start, d)
            if cur not in occ:
                continue
            while cur in occ:
                cur = add(cur, d)
            if self.simulate_ok(pid, cur):
                out.append(cur)
        return out

    def slide_dests(self, pid, exact_steps=None, min_freedom=1):
        if self.piece_freedom(pid) < min_freedom or not self.can_leave(pid):
            return []
        p = self.pieces[pid]
        start = (p["q"], p["r"])
        rest = self.occupied_without(pid)
        if not rest:
            return []

        def touches(cell):
            return any(n in rest for n in neighbors(cell))

        best = {}
        q = deque([(start, 0)])
        seen_depth = {start: 0}
        while q:
            cur, dist = q.popleft()
            if exact_steps is not None and dist == exact_steps and cur != start:
                if cur not in rest and touches(cur):
                    best[cur] = dist
                continue
            if (
                exact_steps is None
                and dist > 0
                and cur != start
                and cur not in rest
                and touches(cur)
            ):
                best[cur] = dist
            if exact_steps is not None and dist >= exact_steps:
                continue
            limit = 20 if exact_steps is None else exact_steps
            if dist >= limit:
                continue
            for nxt in neighbors(cur):
                if nxt in rest:
                    continue
                if nxt != start and not touches(nxt):
                    continue
                if not self.gate_ok(rest, cur, nxt):
                    continue
                nd = dist + 1
                if exact_steps is None:
                    if nxt in seen_depth and seen_depth[nxt] <= nd:
                        continue
                    seen_depth[nxt] = nd
                    q.append((nxt, nd))
                else:
                    key = (nxt, nd)
                    if key in seen_depth:
                        continue
                    seen_depth[key] = nd
                    q.append((nxt, nd))
        return [d for d in best if self.simulate_ok(pid, d)]

    def legal_moves(self, color):
        moves = []
        for pid, p in self.pieces.items():
            if p["color"] != color:
                continue
            stack = self.at((p["q"], p["r"]))
            if not stack or stack[-1][1] != pid:
                continue
            kind = p["kind"]
            if kind == "Q":
                dests = self.queen_dests(pid)
            elif kind == "B":
                dests = self.beetle_dests(pid)
            elif kind == "G":
                dests = self.grasshopper_dests(pid)
            elif kind == "A":
                dests = self.slide_dests(pid, exact_steps=None, min_freedom=ANT_FREEDOM_FLOOR)
            elif kind == "S":
                dests = self.slide_dests(pid, exact_steps=3, min_freedom=1)
            else:
                dests = []
            for d in dests:
                moves.append(move_token(pid, *d))
        return sorted(set(moves))

    def apply(self, tok):
        pid, dest = parse_move(tok)
        p = self.pieces[pid]
        stack = [x for x in self.at(dest) if x[1] != pid]
        new_h = 0 if not stack else stack[-1][2]["h"] + 1
        p["q"], p["r"], p["h"] = dest[0], dest[1], new_h
        if p["color"] == "white":
            self.moves_left -= 1
        self.to_move = "black" if self.to_move == "white" else "white"
        return self


def read_board(path):
    pieces = {}
    moves_left = 0
    to_move = "white"
    in_pieces = False
    for line in Path(path).read_text().splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        if t == "pieces:":
            in_pieces = True
            continue
        if in_pieces:
            parts = t.split()
            pid, qs, rs, hs = parts[0], parts[1], parts[2], parts[3]
            color = "white" if pid.startswith("W") else "black"
            kind = pid.split("-")[1][0]
            pieces[pid] = {
                "color": color,
                "kind": kind,
                "q": int(qs),
                "r": int(rs),
                "h": int(hs),
            }
            continue
        if ":" not in t:
            continue
        k, v = t.split(":", 1)
        k, v = k.strip(), v.strip()
        if k == "moves_left":
            moves_left = int(v)
        elif k == "to_move":
            to_move = v.lower()
    return State(pieces, moves_left, to_move)


def coop_pinable(state):
    memo = {}

    def rec(st):
        if st.pinned():
            return True
        if st.moves_left <= 0:
            return False
        key = fingerprint(st)
        if key in memo:
            return memo[key]
        for mv in st.legal_moves("white"):
            nxt = st.clone()
            nxt.to_move = "white"
            nxt.apply(mv)
            if rec(nxt):
                memo[key] = True
                return True
        memo[key] = False
        return False

    return rec(state.clone())


def coop_sequence(state):
    def rec(st, seq):
        if st.pinned():
            return seq, st.freedom()
        if st.moves_left <= 0:
            return None
        for mv in st.legal_moves("white"):
            nxt = st.clone()
            nxt.to_move = "white"
            nxt.apply(mv)
            got = rec(nxt, seq + [mv])
            if got is not None:
                return got
        return None

    return rec(state.clone(), [])


def force_win_from(state, white_to_move):
    memo = {}

    def rec(st, wtm):
        if st.pinned():
            return True
        key = (*fingerprint(st), wtm)
        if key in memo:
            return memo[key]
        if wtm:
            if st.moves_left <= 0:
                memo[key] = False
                return False
            opts = st.legal_moves("white")
            if not opts:
                memo[key] = False
                return False
            for mv in opts:
                nxt = st.clone()
                nxt.to_move = "white"
                nxt.apply(mv)
                if nxt.pinned() or rec(nxt, False):
                    memo[key] = True
                    return True
            memo[key] = False
            return False
        opts = st.legal_moves("black")
        if not opts:
            memo[key] = rec(st, True)
            return memo[key]
        for mv in opts:
            nxt = st.clone()
            nxt.to_move = "black"
            nxt.apply(mv)
            if not rec(nxt, True):
                memo[key] = False
                return False
        memo[key] = True
        return True

    return rec(state.clone(), white_to_move)


def force_win(state):
    return force_win_from(state, True)


def classify(state):
    if force_win(state):
        return "win"
    if coop_pinable(state):
        return "trap"
    return "fort"


def find_winning_first_moves(state):
    out = []
    for mv in state.legal_moves("white"):
        nxt = state.clone()
        nxt.to_move = "white"
        nxt.apply(mv)
        if nxt.pinned():
            out.append(mv)
            continue
        if force_win_from(nxt, False):
            out.append(mv)
    return sorted(set(out))


def threat_moves(state):
    if state.moves_left < 2:
        return []
    out = []
    for m1 in state.legal_moves("white"):
        mid = state.clone()
        mid.to_move = "white"
        mid.apply(m1)
        if mid.pinned():
            continue
        hit = False
        for m2 in mid.legal_moves("white"):
            end = mid.clone()
            end.to_move = "white"
            end.apply(m2)
            if end.pinned():
                hit = True
                break
        if hit:
            out.append(m1)
    return out


def refutation_reply(state, threat):
    mid = state.clone()
    mid.to_move = "white"
    mid.apply(threat)
    for reply in mid.legal_moves("black"):
        after = mid.clone()
        after.to_move = "black"
        after.apply(reply)
        can_pin = False
        for m2 in after.legal_moves("white"):
            end = after.clone()
            end.to_move = "white"
            end.apply(m2)
            if end.pinned():
                can_pin = True
                break
        if not can_pin:
            return reply
    return None


def _round_files():
    return sorted(PUZZLE_SEAL.glob("board_*.txt"))


def _expected():
    out = {}
    for path in _round_files():
        bid = path.name[:-4]
        state = read_board(path)
        out[bid] = (classify(state), state)
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


def _probe(board_id, move):
    sheet = PUZZLE_SEAL / f"{board_id}.txt"
    proc = subprocess.run(
        [
            "java", "-jar", str(JUDGE_SEAL), "probe",
            "--board", str(sheet), "--move", move,
        ],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0 and proc.stdout, (
        f"judge failed on {board_id}: {proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def _apply_sequence(state, sequence):
    st = state.clone()
    for tok in sequence:
        pid, _dest = parse_move(tok)
        color = st.pieces[pid]["color"]
        st.to_move = color
        assert tok in st.legal_moves(color), f"illegal token {tok}"
        st.apply(tok)
    return st


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
    assert len(ids) == len(set(ids)) == len(expected) == 10
    for r in card["rounds"]:
        assert r["status"] in ("win", "trap", "fort")
        assert isinstance(r["coop_pin"], bool)
        assert isinstance(r.get("key_bug", ""), str)
        assert isinstance(r.get("freedom"), int)
        assert float("-inf") < r["freedom"] < float("inf")
        assert isinstance(r.get("sequence", []), list)
        assert isinstance(r.get("refutations", []), list)


def test_printer_repeats_completed_card(card, tmp_path):
    """Repeated kiosk filing preserves identical completed-card bytes."""
    staged = tmp_path / "hive-card.json"
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


def test_status_matches_search(rounds_by_id, expected):
    """Every status/coop_pin matches an independent search."""
    for bid, (verdict, _state) in expected.items():
        entry = rounds_by_id[bid]
        assert entry["status"] == verdict, bid
        assert entry["coop_pin"] is (verdict != "fort"), bid


def test_win_key_bug_and_sequence(rounds_by_id, expected):
    """Win rounds name a forcing first move and a judge-legal sequence."""
    wins = [b for b, (verdict, _st) in expected.items() if verdict == "win"]
    assert len(wins) >= 3
    for bid in wins:
        _verdict, st = expected[bid]
        wm = set(find_winning_first_moves(st))
        entry = rounds_by_id[bid]
        key = entry.get("key_bug") or ""
        assert key, f"{bid}: win needs a key_bug"
        assert key in wm, f"{bid}: key_bug {key} is not forcing"
        assert not (entry.get("refutations") or [])
        seq = entry.get("sequence") or []
        assert seq, f"{bid}: win needs a sequence"
        assert seq[0] == key, f"{bid}: sequence must start with key_bug"
        probe = _probe(bid, key)
        assert probe.get("legal") is True, f"{bid}: {key} not a legal move"
        res = _validate(bid, ";".join(seq))
        assert res.get("all_legal") is True, f"{bid}: illegal sequence {seq}"
        assert res["black_freedom"] is not None
        assert res["black_freedom"] <= PIN_FLOOR
        assert entry["freedom"] == res["black_freedom"]
        white_steps = [t for t in seq if t.startswith("W-")]
        assert len(white_steps) <= st.moves_left


def test_trap_refutation_coverage(rounds_by_id, expected):
    """Trap rounds cover every threat move with a fighting Black reply."""
    traps = [b for b, (verdict, _st) in expected.items() if verdict == "trap"]
    assert len(traps) >= 3
    for bid in traps:
        _verdict, st = expected[bid]
        required = set(threat_moves(st))
        assert required, f"{bid}: trap should expose threats"
        entry = rounds_by_id[bid]
        assert not (entry.get("key_bug") or "")
        assert not (entry.get("sequence") or [])
        refs = entry.get("refutations") or []
        covered = {r["move"] for r in refs}
        missing = sorted(required - covered)
        assert not missing, f"{bid}: uncovered threats {missing}"
        assert entry["freedom"] <= PIN_FLOOR
        for ref in refs:
            move, reply = ref["move"], ref["reply"]
            res = _validate(bid, f"{move};{reply}")
            assert res.get("all_legal") is True, (
                f"{bid}: illegal refutation {move}/{reply}"
            )
            mid = st.clone()
            mid.to_move = "white"
            mid.apply(move)
            mid.to_move = "black"
            assert reply in mid.legal_moves("black"), (
                f"{bid}: reply {reply} is not a legal Black answer"
            )
            after = mid.clone()
            after.apply(reply)
            hit = False
            for m2 in after.legal_moves("white"):
                end = after.clone()
                end.to_move = "white"
                end.apply(m2)
                if end.pinned():
                    hit = True
                    break
            assert not hit, f"{bid}: reply {reply} fails to refute {move}"


def test_fort_rows(rounds_by_id, expected):
    """Fort rounds cannot reach the floor even with Black passing."""
    forts = [b for b, (verdict, _st) in expected.items() if verdict == "fort"]
    assert len(forts) >= 1
    for bid in forts:
        entry = rounds_by_id[bid]
        _verdict, st = expected[bid]
        assert entry["status"] == "fort"
        assert entry["coop_pin"] is False
        assert not (entry.get("key_bug") or "")
        assert not (entry.get("sequence") or [])
        assert not (entry.get("refutations") or [])
        assert entry["freedom"] == st.freedom()
        assert not coop_pinable(st)


def test_sensei_is_not_the_verdict(rounds_by_id, expected):
    """Rounds the surface whisper calls pinned are not all wins."""
    proc = subprocess.run(
        ["bash", "/app/tools/sensei_hint.sh", str(PUZZLE_SEAL)],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    pinned_look = {
        line.split()[0]
        for line in proc.stdout.splitlines()
        if line.strip().endswith("looks_pinned")
    }
    trap_ids = {b for b, (verdict, _st) in expected.items() if verdict == "trap"}
    assert trap_ids <= pinned_look
    for bid in trap_ids:
        assert rounds_by_id[bid]["status"] == "trap"


def test_freedom_not_padded(rounds_by_id, expected):
    """Win freedom equals the true Black queen freedom after the sequence."""
    for bid, (verdict, state) in expected.items():
        if verdict != "win":
            continue
        entry = rounds_by_id[bid]
        seq = entry.get("sequence") or []
        end = _apply_sequence(state, seq)
        actual = end.freedom()
        assert actual == entry["freedom"], bid
        assert actual <= PIN_FLOOR, bid


def test_sequence_uses_move_budget(rounds_by_id, expected):
    """Win sequences never spend more White moves than moves_left."""
    for bid, (verdict, state) in expected.items():
        if verdict != "win":
            continue
        entry = rounds_by_id[bid]
        seq = entry.get("sequence") or []
        white_used = sum(1 for t in seq if t.split(">")[0].startswith("W-"))
        assert white_used <= state.moves_left, bid
        assert white_used >= 1, bid
