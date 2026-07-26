"""Verifier for the Nine Men's Morris mill-fork contest card.

Independently classifies each round (win / trap / fort) from the sealed
puzzle sheets with a self-contained Morris search, then checks the
submitted card. Legality of moves, mills, and removals is confirmed with
the sealed judge.jar; the win/trap/fort verdicts are recomputed here.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from itertools import combinations
from pathlib import Path

CARD_PATH = Path("/output/morris-card.json")
JUDGE = Path("/app/bin/judge.jar")
JUDGE_SEAL = Path("/opt/tbench/judge.jar")
PUZZLE_DIR = Path("/app/puzzles")
PUZZLE_SEAL = Path("/opt/tbench/puzzles")

POINTS = (
    "a7", "d7", "g7",
    "b6", "d6", "f6",
    "c5", "d5", "e5",
    "a4", "b4", "c4", "e4", "f4", "g4",
    "c3", "d3", "e3",
    "b2", "d2", "f2",
    "a1", "d1", "g1",
)

ADJ = {
    "a7": ("d7", "a4"),
    "d7": ("a7", "g7", "d6"),
    "g7": ("d7", "g4"),
    "b6": ("d6", "b4"),
    "d6": ("d7", "b6", "f6", "d5"),
    "f6": ("d6", "f4"),
    "c5": ("d5", "c4"),
    "d5": ("d6", "c5", "e5"),
    "e5": ("d5", "e4"),
    "a4": ("a7", "b4", "a1"),
    "b4": ("b6", "a4", "c4", "b2"),
    "c4": ("c5", "b4", "c3"),
    "e4": ("e5", "f4", "e3"),
    "f4": ("f6", "e4", "g4", "f2"),
    "g4": ("g7", "f4", "g1"),
    "c3": ("c4", "d3"),
    "d3": ("c3", "e3", "d2"),
    "e3": ("e4", "d3"),
    "b2": ("b4", "d2"),
    "d2": ("d3", "b2", "f2", "d1"),
    "f2": ("f4", "d2"),
    "a1": ("a4", "d1"),
    "d1": ("a1", "g1", "d2"),
    "g1": ("g4", "d1"),
}

MILLS = (
    ("a7", "d7", "g7"),
    ("a1", "d1", "g1"),
    ("a7", "a4", "a1"),
    ("g7", "g4", "g1"),
    ("b6", "d6", "f6"),
    ("b2", "d2", "f2"),
    ("b6", "b4", "b2"),
    ("f6", "f4", "f2"),
    ("c5", "d5", "e5"),
    ("c3", "d3", "e3"),
    ("c5", "c4", "c3"),
    ("e5", "e4", "e3"),
    ("a4", "b4", "c4"),
    ("e4", "f4", "g4"),
    ("d7", "d6", "d5"),
    ("d3", "d2", "d1"),
)

MILL_FLOOR = 1
FLY_COUNT = 3
SCHEMA_TAG = "morris-mill-v1"


def _ch(side: str) -> str:
    return "W" if side == "white" else "B"


def _side(ch: str) -> str:
    return "white" if ch == "W" else "black"


class State:
    __slots__ = ("board", "moves_left", "pending_mills", "pending_remove", "to_move")

    def __init__(
        self,
        board,
        to_move="white",
        moves_left=3,
        pending_remove=None,
        pending_mills=0,
    ):
        self.board = {p: board.get(p) for p in POINTS}
        self.to_move = to_move
        self.moves_left = int(moves_left)
        self.pending_remove = pending_remove
        self.pending_mills = int(pending_mills)

    def clone(self):
        return State(
            dict(self.board),
            self.to_move,
            self.moves_left,
            self.pending_remove,
            self.pending_mills,
        )

    def fp(self):
        return (
            tuple(self.board[p] for p in POINTS),
            self.to_move,
            self.moves_left,
            self.pending_remove,
            self.pending_mills,
        )

    def count(self, side: str) -> int:
        c = _ch(side)
        return sum(1 for p in POINTS if self.board[p] == c)

    def flying(self, side: str) -> bool:
        return self.count(side) <= FLY_COUNT

    def occupied(self, side: str):
        c = _ch(side)
        return [p for p in POINTS if self.board[p] == c]

    def empty(self):
        return [p for p in POINTS if self.board[p] is None]

    def mills_at(self, point: str, side: str):
        c = _ch(side)
        return [m for m in MILLS if point in m and all(self.board[x] == c for x in m)]

    def in_mill(self, point: str) -> bool:
        v = self.board[point]
        if v is None:
            return False
        return bool(self.mills_at(point, _side(v)))

    def removable(self, victim: str):
        pts = self.occupied(victim)
        free = [p for p in pts if not self.in_mill(p)]
        return free if free else list(pts)

    def dests(self, fr: str, side: str):
        if self.board[fr] != _ch(side):
            return []
        if self.flying(side):
            return list(self.empty())
        return [d for d in ADJ[fr] if self.board[d] is None]

    def slides(self, side: str):
        return [(fr, to) for fr in self.occupied(side) for to in self.dests(fr, side)]


def move_token(fr: str, to: str, side: str) -> str:
    return f"{_ch(side)}:{fr}-{to}"


def parse_token(tok: str):
    if tok in ("B:pass", "W:pass", "pass"):
        return ("black" if tok.startswith("B") else "white"), "pass", "pass"
    ch, rest = tok.split(":", 1)
    fr, to = rest.split("-", 1)
    return _side(ch), fr, to


def _end_turn(st: State, side: str) -> State:
    nxt = st.clone()
    nxt.pending_remove = None
    nxt.pending_mills = 0
    if side == "white":
        nxt.moves_left -= 1
    nxt.to_move = "black" if side == "white" else "white"
    return nxt


def apply_slide(st: State, fr: str, to: str) -> tuple[State, int]:
    side = st.to_move
    assert st.pending_remove is None
    assert (fr, to) in st.slides(side)
    nxt = st.clone()
    nxt.board[fr] = None
    nxt.board[to] = _ch(side)
    mills = len(nxt.mills_at(to, side))
    if mills:
        nxt.pending_remove = side
        nxt.pending_mills = mills
        return nxt, mills
    return _end_turn(nxt, side), 0


def apply_remove(st: State, point: str) -> State:
    assert st.pending_remove is not None and st.pending_mills > 0
    side = st.pending_remove
    victim = "black" if side == "white" else "white"
    assert point in st.removable(victim)
    nxt = st.clone()
    nxt.board[point] = None
    nxt.pending_mills -= 1
    if nxt.pending_mills > 0:
        nxt.pending_remove = side
        return nxt
    return _end_turn(nxt, side)


def white_actions(st: State):
    """Yield (seq_tokens, removals, new_state, mills, key_point)."""
    assert st.to_move == "white" and st.pending_remove is None
    if st.moves_left <= 0:
        return
    for fr, to in st.slides("white"):
        mid, mills = apply_slide(st, fr, to)
        tok = move_token(fr, to, "white")
        if mills == 0:
            yield [tok], [], mid, 0, ""
            continue
        opts = mid.removable("black")
        if mills == 1:
            for pt in opts:
                yield [tok], [pt], apply_remove(mid, pt), 1, to
        else:
            for combo in combinations(sorted(opts), mills):
                cur = mid.clone()
                ok = True
                used = []
                for i, pt in enumerate(combo):
                    if pt not in cur.removable("black"):
                        ok = False
                        break
                    used.append(pt)
                    cur = apply_remove(cur, pt)
                if ok:
                    yield [tok], used, cur, mills, to


def black_actions(st: State):
    assert st.to_move == "black" and st.pending_remove is None
    slides = st.slides("black")
    if not slides:
        nxt = st.clone()
        nxt.to_move = "white"
        yield ["B:pass"], [], nxt, 0
        return
    for fr, to in slides:
        mid, mills = apply_slide(st, fr, to)
        tok = move_token(fr, to, "black")
        if mills == 0:
            yield [tok], [], mid, 0
            continue
        opts = mid.removable("white")
        if mills == 1:
            for pt in opts:
                yield [tok], [pt], apply_remove(mid, pt), mills
        else:
            for combo in combinations(sorted(opts), mills):
                cur = mid.clone()
                ok = True
                for pt in combo:
                    if pt not in cur.removable("white"):
                        ok = False
                        break
                    cur = apply_remove(cur, pt)
                if ok:
                    yield [tok], list(combo), cur, mills


_FORCE_CACHE: dict = {}
_COOP_CACHE: dict = {}


def clear_caches():
    _FORCE_CACHE.clear()
    _COOP_CACHE.clear()


def force_mill(st: State) -> bool:
    """White can force forming ≥ MILL_FLOOR mills against fighting Black."""

    def wplay(s: State) -> bool:
        key = ("w", s.fp())
        if key in _FORCE_CACHE:
            return _FORCE_CACHE[key]
        if s.moves_left <= 0:
            _FORCE_CACHE[key] = False
            return False
        for _toks, _rems, nxt, mills, _k in white_actions(s):
            if mills >= MILL_FLOOR:
                _FORCE_CACHE[key] = True
                return True
            if not bhold(nxt):
                _FORCE_CACHE[key] = True
                return True
        _FORCE_CACHE[key] = False
        return False

    def bhold(s: State) -> bool:
        """True if Black can still prevent a forced mill."""
        key = ("b", s.fp())
        if key in _FORCE_CACHE:
            return _FORCE_CACHE[key]
        if s.to_move != "black":
            val = not wplay(s)
            _FORCE_CACHE[key] = val
            return val
        holds = False
        for _toks, _rems, nxt, _m in black_actions(s):
            if not wplay(nxt):
                holds = True
                break
        _FORCE_CACHE[key] = holds
        return holds

    clear_caches()
    return wplay(st.clone())


def coop_mill(st: State):
    """Black always passes. Returns (ok, sequence, removals, mill_in, key_point)."""

    def dfs(s: State, seq, rems, acc, key):
        fk = (s.fp(), acc)
        if fk in _COOP_CACHE:
            return None
        _COOP_CACHE[fk] = True
        if acc >= MILL_FLOOR:
            return seq, rems, acc, key
        if s.moves_left <= 0 or s.to_move != "white":
            return None
        for toks, rem, nxt, mills, k in white_actions(s):
            nseq = seq + toks
            nrem = rems + rem
            nacc = acc + mills
            nkey = k if mills else key
            if nacc >= MILL_FLOOR:
                return nseq, nrem, nacc, nkey
            # black passes
            if nxt.to_move == "black":
                passed = nxt.clone()
                passed.to_move = "white"
                nxt = passed
            got = dfs(nxt, nseq, nrem, nacc, nkey)
            if got:
                return got
        return None

    _COOP_CACHE.clear()
    got = dfs(st.clone(), [], [], 0, "")
    if got is None:
        return False, [], [], 0, ""
    return True, got[0], got[1], got[2], got[3]


def classify(st: State) -> str:
    if force_mill(st):
        return "win"
    ok, *_ = coop_mill(st)
    if ok:
        return "trap"
    return "fort"


def threat_moves(st: State) -> list[str]:
    out = []
    for toks, _rem, nxt, mills, _k in white_actions(st):
        if mills >= MILL_FLOOR:
            continue
        tok = toks[0]
        cur = nxt.clone()
        if cur.to_move == "black":
            cur.to_move = "white"
        if cur.moves_left <= 0:
            continue
        for _t2, _r2, _n2, m2, _ in white_actions(cur):
            if m2 >= MILL_FLOOR:
                out.append(tok)
                break
    return sorted(set(out))


def refutation_reply(st: State, threat: str) -> str | None:
    match = None
    for toks, _rem, nxt, mills, _k in white_actions(st):
        if toks[0] == threat and mills < MILL_FLOOR:
            match = nxt
            break
    if match is None or match.to_move != "black":
        return None
    for btoks, _br, after, _m in black_actions(match):
        if after.to_move != "white":
            continue
        can = any(m >= MILL_FLOOR for _t, _r, _n, m, _ in white_actions(after))
        if not can:
            return btoks[0]
    return None


def find_forcing_line(st: State):
    if not force_mill(st):
        return None

    def build(s, seq, rems, acc, key):
        if acc >= MILL_FLOOR:
            return seq, rems, acc, key
        if s.to_move != "white" or s.moves_left <= 0:
            return None
        cands = []
        for toks, rem, nxt, mills, k in white_actions(s):
            nseq = seq + toks
            nrem = rems + rem
            nacc = acc + mills
            nkey = k if mills else key
            if nacc >= MILL_FLOOR:
                return nseq, nrem, nacc, nkey
            # preserves force against all black replies?
            if preserves(nxt):
                cands.append((toks[0], nxt, nseq, nrem, nacc, nkey))
        for _tok, nxt, nseq, nrem, nacc, nkey in sorted(cands, key=lambda x: x[0]):
            got = extend_black(nxt, nseq, nrem, nacc, nkey)
            if got:
                return got
        return None

    def preserves(s):
        if s.to_move != "black":
            return force_mill(s)
        for _t, _r, after, _m in black_actions(s):
            if not force_mill(after):
                return False
        return True

    def extend_black(s, seq, rems, acc, key):
        acts = list(black_actions(s))
        # concrete PV: lex-min black reply, then continue
        btoks, _br, after, _m = min(acts, key=lambda x: x[0][0])
        return build(after, seq + btoks, rems, acc, key)

    clear_caches()
    return build(st.clone(), [], [], 0, "")


def parse_board_file(path: str) -> State:
    meta = {}
    board = {p: None for p in POINTS}
    mode = None
    with open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line in ("board:", "white:", "black:"):
                mode = line[:-1]
                continue
            if mode is None and ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
                continue
            if mode == "board":
                for tok in line.split():
                    pt, ch = tok.split("=", 1)
                    board[pt] = None if ch in (".", "-") else ch
            elif mode in ("white", "black"):
                for pt in line.split():
                    board[pt] = "W" if mode == "white" else "B"
    return State(board, meta.get("to_move", "white"), int(meta.get("moves_left", "3")))


def _load_card():
    assert CARD_PATH.is_file(), "missing /output/morris-card.json"
    return json.loads(CARD_PATH.read_text())


def _boards():
    return sorted(PUZZLE_DIR.glob("board_*.txt"))


def _judge_validate(board, sequence, removals):
    cmd = [
        "java", "-jar", str(JUDGE_SEAL), "validate",
        "--board", str(board),
        "--moves", ";".join(sequence),
        "--removals", ";".join(removals),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def _row_by_id(card):
    return {r["board_id"]: r for r in card["rounds"]}


def test_a1_onyx_card_reads_as_a_tournament_card():
    """Card carries schema_tag and every round with the required fields."""
    card = _load_card()
    assert card.get("schema_tag") == SCHEMA_TAG
    rounds = card["rounds"]
    assert len(rounds) == 10
    assert [r["board_id"] for r in rounds] == [p.stem for p in _boards()]
    allowed = {"win", "trap", "fort"}
    for r in rounds:
        assert r["status"] in allowed
        assert isinstance(r["coop_fork"], bool)
        assert isinstance(r["key_point"], str)
        assert isinstance(r["mill_in"], int)
        assert isinstance(r["sequence"], list)
        assert isinstance(r["removals"], list)
        assert isinstance(r["refutations"], list)
        assert r["coop_fork"] == (r["status"] != "fort")
        if r["status"] == "fort":
            assert r["mill_in"] == 0
            assert r["sequence"] == []
            assert r["removals"] == []
            assert r["refutations"] == []
            assert r["key_point"] == ""
        if r["status"] == "trap":
            assert r["sequence"] == []
            assert r["removals"] == []
            assert r["key_point"] == ""
            assert r["mill_in"] >= MILL_FLOOR
            assert r["refutations"], "trap needs refutations"
        if r["status"] == "win":
            assert r["sequence"], "win needs a forcing line"
            assert r["key_point"]
            assert r["mill_in"] >= MILL_FLOOR


def test_c3_slate_sealed_judge_and_sheets_stay_intact():
    """Sealed judge and puzzle sheets match verifier-owned seal copies."""
    assert JUDGE.is_file() and JUDGE_SEAL.is_file()
    assert JUDGE.read_bytes() == JUDGE_SEAL.read_bytes()
    live = {p.name: p.read_bytes() for p in _boards()}
    sealed = {p.name: p.read_bytes() for p in sorted(PUZZLE_SEAL.glob("board_*.txt"))}
    assert live == sealed
    sample = next(iter(sorted(PUZZLE_SEAL.glob("board_*.txt"))))
    out = subprocess.run(
        ["java", "-jar", str(JUDGE_SEAL), "view", "--board", str(sample)],
        capture_output=True, text=True, check=False,
    )
    assert out.returncode == 0
    data = json.loads(out.stdout)
    assert "moves_left" in data


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Every status matches an independent mill-force search on the sheets."""
    card = _load_card()
    rows = _row_by_id(card)
    ok = 0
    for path in _boards():
        st = parse_board_file(str(path))
        expected = classify(st)
        got = rows[path.stem]["status"]
        if got == expected:
            ok += 1
        else:
            print("mismatch", path.stem, "expected", expected, "got", got)
    assert ok >= 9, f"verdict matches {ok}/10"


def test_g2_flint_forcing_lines_really_force():
    """Win lines replay through the sealed judge and really force a mill."""
    card = _load_card()
    wins = [r for r in card["rounds"] if r["status"] == "win"]
    assert len(wins) >= 3
    forced_ok = 0
    for row in wins:
        path = PUZZLE_DIR / f"{row['board_id']}.txt"
        st = parse_board_file(str(path))
        assert force_mill(st)
        data = _judge_validate(path, row["sequence"], row["removals"])
        assert data["all_legal"] is True
        assert int(data["mill_total"]) == row["mill_in"]
        assert row["mill_in"] >= MILL_FLOOR
        assert row["key_point"]
        # White drop count spent <= moves_left
        white_turns = sum(1 for t in row["sequence"] if t.startswith("W:"))
        assert white_turns <= st.moves_left
        forced_ok += 1
    assert forced_ok == len(wins)


def test_j4_amber_trap_refutations_cover_every_threat():
    """Trap rounds cover every threat move with a fighting Black reply."""
    card = _load_card()
    traps = [r for r in card["rounds"] if r["status"] == "trap"]
    assert len(traps) >= 3
    for row in traps:
        path = PUZZLE_DIR / f"{row['board_id']}.txt"
        st = parse_board_file(str(path))
        assert not force_mill(st)
        ok, _seq, _rems, mill_in, _key = coop_mill(st)
        assert ok
        assert row["mill_in"] == mill_in
        required = set(threat_moves(st))
        submitted = {ref["move"] for ref in row["refutations"]}
        assert required <= submitted, (row["board_id"], required - submitted)
        for ref in row["refutations"]:
            assert _reply_refutes(st, ref["move"], ref["reply"]), (
                row["board_id"],
                ref,
            )
            if ref["move"] in required:
                # preferred reply from search must work; extras may differ
                pass


def _reply_refutes(st, threat, reply_tok):
    match = None
    for toks, _rem, nxt, mills, _k in white_actions(st):
        if toks[0] == threat and mills < MILL_FLOOR:
            match = nxt
            break
    if match is None or match.to_move != "black":
        return False
    for btoks, _br, after, _m in black_actions(match):
        if btoks[0] != reply_tok:
            continue
        if after.to_move != "white":
            return False
        can = any(m >= MILL_FLOOR for _t, _r, _n, m, _ in white_actions(after))
        return not can
    return False


def test_m8_jade_forts_are_not_the_kiosk_cheer():
    """Fort rounds cannot close a mill even with Black passing."""
    card = _load_card()
    forts = [r for r in card["rounds"] if r["status"] == "fort"]
    assert len(forts) >= 1
    for row in forts:
        path = PUZZLE_DIR / f"{row['board_id']}.txt"
        st = parse_board_file(str(path))
        assert classify(st) == "fort"
        assert row["mill_in"] == 0
        assert row["coop_fork"] is False


def test_p5_quartz_printer_repeats_completed_card():
    """Repeated kiosk filing preserves identical completed-card bytes."""
    card = _load_card()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "morris-card.json"
        path.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n")
        command = ["bash", "/app/kiosk/emit_card.sh", str(path)]
        first_run = subprocess.run(
            command, capture_output=True, text=True, check=False
        )
        assert first_run.returncode == 0, first_run.stderr
        first = path.read_bytes()
        second_run = subprocess.run(
            command, capture_output=True, text=True, check=False
        )
        assert second_run.returncode == 0, second_run.stderr
        assert path.read_bytes() == first


def test_r2_topaz_sensei_is_not_the_verdict():
    """Rounds the surface whisper calls open are not all wins."""
    card = _load_card()
    out = subprocess.run(
        ["bash", "/app/tools/sensei_hint.sh", str(PUZZLE_SEAL)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0
    whisper = {}
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            whisper[parts[0]] = parts[1]
    # Sensei cheers mills on traps; card must still call them traps.
    traps = [r for r in card["rounds"] if r["status"] == "trap"]
    cheered = [r for r in traps if whisper.get(r["board_id"]) == "looks_mill"]
    assert cheered, "expected sensei false-green on at least one trap"
    # And at least one fort exists in the booklet
    forts = [r["board_id"] for r in card["rounds"] if r["status"] == "fort"]
    assert forts


def test_t7_opal_whole_booklet_stands_up():
    """At least nine rounds stand up under search plus judge replay."""
    card = _load_card()
    rows = _row_by_id(card)
    score = 0
    for path in _boards():
        st = parse_board_file(str(path))
        exp = classify(st)
        row = rows[path.stem]
        if row["status"] != exp:
            continue
        if exp == "win":
            data = _judge_validate(path, row["sequence"], row["removals"])
            if data.get("all_legal") and int(data.get("mill_total", 0)) == row["mill_in"]:
                score += 1
        elif exp == "trap":
            req = set(threat_moves(st))
            sub = {ref["move"] for ref in row["refutations"]}
            if req <= sub and row["mill_in"] >= MILL_FLOOR:
                score += 1
        else:
            if row["mill_in"] == 0 and row["coop_fork"] is False:
                score += 1
    assert score >= 9, f"booklet standing {score}/10"
