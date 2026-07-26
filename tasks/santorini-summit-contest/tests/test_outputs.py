"""Verifier for the Santorini summit contest card.

Independently classifies each round (win / trap / fort) from the sealed
puzzle sheets with a self-contained Santorini search, then checks the
submitted card. Legality of move+build lines is confirmed with the sealed
judge.jar; the win/trap/fort verdicts are recomputed here. Sensei and kiosk
drafts are bait only.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

FILES = "abcde"
RANKS = "12345"
SQUARES = [f + r for r in RANKS for f in FILES]
IDX = {sq: i for i, sq in enumerate(SQUARES)}
DIRS = [(df, dr) for df in (-1, 0, 1) for dr in (-1, 0, 1) if not (df == 0 and dr == 0)]


def nbrs(sq: str) -> list[str]:
    f, r = FILES.index(sq[0]), int(sq[1]) - 1
    out = []
    for df, dr in DIRS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 5 and 0 <= nr < 5:
            out.append(FILES[nf] + str(nr + 1))
    return out


class State:
    __slots__ = ("budget", "h", "occ", "to_move")

    def __init__(self, h, first, second, to_move="first", budget=2):
        self.h = list(h)  # 0..3 or 4=dome
        self.occ = {sq: None for sq in SQUARES}
        for sq in first:
            self.occ[sq] = "F"
        for sq in second:
            self.occ[sq] = "S"
        self.to_move = to_move
        self.budget = int(budget)

    def clone(self):
        n = State.__new__(State)
        n.h = self.h[:]
        n.occ = dict(self.occ)
        n.to_move = self.to_move
        n.budget = self.budget
        return n

    def workers(self, side: str) -> list[str]:
        ch = "F" if side == "first" else "S"
        return [sq for sq in SQUARES if self.occ[sq] == ch]

    def height(self, sq: str) -> int:
        return self.h[IDX[sq]]

    def is_dome(self, sq: str) -> bool:
        return self.h[IDX[sq]] >= 4

    def legal_moves(self, side: str | None = None) -> list[str]:
        side = side or self.to_move
        ch = "F" if side == "first" else "S"
        toks = []
        for fr in self.workers(side):
            hf = self.height(fr)
            for to in nbrs(fr):
                if self.occ[to] is not None or self.is_dome(to):
                    continue
                ht = self.height(to)
                if ht - hf > 1:
                    continue
                # Winning ascent: move onto 3, no build.
                if ht == 3:
                    toks.append(f"{ch}:{fr}-{to}")
                    continue
                for b in nbrs(to):
                    # After leaving fr, fr is empty and buildable when adjacent.
                    if b != fr and self.occ[b] is not None:
                        continue
                    if self.is_dome(b):
                        continue
                    toks.append(f"{ch}:{fr}-{to}:{b}")
        return sorted(set(toks))

    def apply(self, tok: str) -> State:
        side = "first" if tok[0] == "F" else "second"
        assert side == self.to_move, (tok, self.to_move)
        body = tok[2:]
        if ":" in body.split("-", 1)[-1] if False else True:
            pass
        parts = body.split(":")
        if len(parts) == 1:
            fr, to = parts[0].split("-")
            build = None
        else:
            fr_to, build = parts[0], parts[1]
            fr, to = fr_to.split("-")
        nxt = self.clone()
        assert nxt.occ[fr] == ("F" if side == "first" else "S")
        nxt.occ[fr] = None
        nxt.occ[to] = "F" if side == "first" else "S"
        ht = nxt.height(to)
        if ht == 3:
            assert build is None
            # win — turn ends; budget spent for first
            if side == "first":
                nxt.budget -= 1
            nxt.to_move = "second" if side == "first" else "first"
            return nxt
        assert build is not None
        bi = IDX[build]
        assert nxt.occ[build] is None or build == fr  # fr already cleared
        assert nxt.h[bi] < 4
        nxt.h[bi] += 1
        if nxt.h[bi] > 3:
            nxt.h[bi] = 4  # dome after building on 3
        if side == "first":
            nxt.budget -= 1
        nxt.to_move = "second" if side == "first" else "first"
        return nxt

    def first_summited(self, tok: str) -> bool:
        if not tok.startswith("F:"):
            return False
        body = tok[2:]
        if ":" in body:
            fr_to = body.split(":")[0]
        else:
            fr_to = body
        _fr, to = fr_to.split("-")
        return self.height(to) == 3

    def dump(self) -> str:
        rows = []
        for r in range(5, 0, -1):
            cells = []
            for f in FILES:
                sq = f + str(r)
                h = self.height(sq)
                hs = "D" if h >= 4 else str(h)
                w = self.occ[sq] or "."
                cells.append(hs + w)
            rows.append(" ".join(cells))
        return "\n".join(rows)


def parse_token_summit_delta(st: State, tok: str) -> int:
    body = tok[2:]
    fr_to = body.split(":")[0]
    fr, to = fr_to.split("-")
    return st.height(to) - st.height(fr)


def coop_summit(st: State, budget: int | None = None) -> tuple[bool, list[str], int]:
    """First-only plan; Second passes (to_move stays/skips). Returns (ok, line, height_delta)."""
    budget = st.budget if budget is None else budget
    # BFS on first-only turns
    from collections import deque

    start = st.clone()
    start.to_move = "first"
    start.budget = budget
    q = deque([(start, [])])
    seen = set()
    while q:
        cur, line = q.popleft()
        if cur.budget < 0:
            continue
        key = (tuple(cur.h), tuple(cur.occ[s] for s in SQUARES), cur.budget)
        if key in seen:
            continue
        seen.add(key)
        if cur.to_move != "first":
            # skip second
            cur = cur.clone()
            cur.to_move = "first"
        if cur.budget <= 0 and not line:
            continue
        moves = sorted(cur.legal_moves("first"), key=lambda t: (0 if cur.first_summited(t) else 1, t))
        for tok in moves:
            if cur.first_summited(tok):
                delta = parse_token_summit_delta(cur, tok)
                return True, line + [tok], delta
            if cur.budget <= 1:
                continue
            nxt = cur.apply(tok)
            # after apply, to_move is second — force back to first without spending
            nxt.to_move = "first"
            # budget already decremented
            q.append((nxt, line + [tok]))
    return False, [], 0


def force_win(st: State, budget: int | None = None) -> tuple[bool, list[str], int]:
    budget = st.budget if budget is None else budget
    memo: dict = {}

    def first_can(cur: State) -> tuple[bool, list[str], int]:
        if cur.budget <= 0:
            return False, [], 0
        key = (tuple(cur.h), tuple(cur.occ[s] for s in SQUARES), cur.budget, "F")
        if key in memo:
            return memo[key]
        moves = sorted(cur.legal_moves("first"), key=lambda t: (0 if cur.first_summited(t) else 1, t))
        for tok in moves:
            if cur.first_summited(tok):
                delta = parse_token_summit_delta(cur, tok)
                memo[key] = (True, [tok], delta)
                return memo[key]
            nxt = cur.apply(tok)
            # Second replies
            ok_all, reply_line, delta = second_fails_to_stop(nxt)
            if ok_all:
                memo[key] = (True, [tok] + reply_line, delta)
                return memo[key]
        memo[key] = (False, [], 0)
        return memo[key]

    def second_fails_to_stop(cur: State) -> tuple[bool, list[str], int]:
        # After First moved; Second to move. First still wins after EVERY Second reply.
        key = (tuple(cur.h), tuple(cur.occ[s] for s in SQUARES), cur.budget, "S")
        if key in memo:
            return memo[key]
        replies = cur.legal_moves("second")
        if not replies:
            # Second passes — First continues
            nxt = cur.clone()
            nxt.to_move = "first"
            ok, line, delta = first_can(nxt)
            memo[key] = (ok, line, delta)
            return memo[key]
        # Need one concrete line for the card: pick any reply and show continuation
        # But ALL replies must leave First able to force.
        witness = None
        for rep in replies:
            nxt = cur.apply(rep)
            ok, line, delta = first_can(nxt)
            if not ok:
                memo[key] = (False, [], 0)
                return memo[key]
            if witness is None:
                witness = ([rep] + line, delta)
        memo[key] = (True, witness[0], witness[1])
        return memo[key]

    return first_can(st.clone())


def threats(st: State) -> list[str]:
    """Non-summit first turns that leave a coop summit on the next First turn."""
    out = []
    for tok in st.legal_moves("first"):
        if st.first_summited(tok):
            continue
        nxt = st.apply(tok)
        nxt.to_move = "first"  # Second passes
        # budget already -1
        ok, _line, _d = coop_summit(nxt, budget=1)
        # also allow remaining budget
        if not ok:
            ok, _line, _d = coop_summit(nxt, budget=max(1, nxt.budget))
        if ok:
            # stricter: exists second First move that summits immediately
            immediate = False
            for t2 in nxt.legal_moves("first"):
                if nxt.first_summited(t2):
                    immediate = True
                    break
            if immediate:
                out.append(tok)
    return out


def classify(st: State) -> dict:
    fw, fline, fd = force_win(st)
    cw, cline, cd = coop_summit(st)
    if fw:
        status = "win"
        coop = True
        return {
            "status": status,
            "coop_summit": coop,
            "sequence": fline,
            "height_delta": fd,
            "key_move": fline[0] if fline else "",
            "refutations": [],
            "threats": [],
        }
    if cw:
        th = threats(st)
        refs = []
        for th_tok in th:
            # find a Second reply that kills immediate follow-up summit
            mid = st.apply(th_tok)
            found = None
            for rep in mid.legal_moves("second"):
                after = mid.apply(rep)
                after.to_move = "first"
                can = any(after.first_summited(t) for t in after.legal_moves("first"))
                if not can:
                    found = rep
                    break
            if found is None:
                # if no refutation exists, this "threat" is actually still forcing-ish;
                # still list threat but skip — for traps Second should be able to answer
                continue
            refs.append({"move": th_tok, "reply": found})
        return {
            "status": "trap",
            "coop_summit": True,
            "sequence": [],
            "height_delta": cd,
            "key_move": "",
            "refutations": refs,
            "threats": th,
            "coop_line": cline,
        }
    return {
        "status": "fort",
        "coop_summit": False,
        "sequence": [],
        "height_delta": 0,
        "key_move": "",
        "refutations": [],
        "threats": [],
    }


def make(h5, first, second, budget=2):
    """h5[0] is rank 5 (top), h5[4] is rank 1 (bottom); each row a..e."""
    flat = [0] * 25
    for ri, row in enumerate(h5):
        rank = 5 - ri
        for ci, v in enumerate(row):
            sq = FILES[ci] + str(rank)
            flat[IDX[sq]] = 4 if v in (4, "D") else int(v)
    return State(flat, first, second, "first", budget)


def write_puzzle(path, board_id, st, note=""):
    lines = [
        f"board_id: {board_id}",
        "to_move: first",
        f"budget: {st.budget}",
        "heights:",
    ]
    for r in range(5, 0, -1):
        row = []
        for f in FILES:
            h = st.height(f + str(r))
            row.append("D" if h >= 4 else str(h))
        lines.append(" ".join(row))
    lines.append("first: " + " ".join(st.workers("first")))
    lines.append("second: " + " ".join(st.workers("second")))
    if note:
        lines.append(f"# {note}")
    path.write_text("\n".join(lines) + "\n")



def load_puzzle(path):
    path = str(path)
    budget = 2
    height_rows = []
    first = []
    second = []
    in_h = False
    board_id = None
    with open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("board_id:"):
                board_id = line.split(":", 1)[1].strip()
            elif line.startswith("budget:"):
                budget = int(line.split(":", 1)[1].strip())
            elif line == "heights:":
                in_h = True
            elif line.startswith("first:"):
                in_h = False
                first = line.split(":", 1)[1].split()
            elif line.startswith("second:"):
                in_h = False
                second = line.split(":", 1)[1].split()
            elif in_h:
                height_rows.append([4 if c == "D" else int(c) for c in line.split()])
    st = make(height_rows, first, second, budget=budget)
    return board_id or Path(path).stem, st


def classify_round(st):
    return classify(st)


def row_from_class(board_id, c):
    return {
        "board_id": board_id,
        "status": c["status"],
        "coop_summit": bool(c["coop_summit"]),
        "key_move": c.get("key_move") or "",
        "sequence": list(c.get("sequence") or []),
        "refutations": list(c.get("refutations") or []),
    }



CARD_PATH = Path("/app/answers.json")
JUDGE = Path("/app/bin/judge.jar")
JUDGE_SEAL = Path("/opt/tbench/judge.jar")
PUZZLE_DIR = Path("/app/puzzles")
PUZZLE_SEAL = Path("/opt/tbench/puzzles")


def _load_card():
    assert CARD_PATH.is_file(), "missing /app/answers.json"
    return json.loads(CARD_PATH.read_text())


def _expected():
    rows = {}
    for path in sorted(PUZZLE_DIR.glob("board_*.txt")):
        bid, st = load_puzzle(path)
        rows[bid] = row_from_class(bid, classify_round(st))
    return rows


def _judge_validate(board_id, sequence):
    board = str(PUZZLE_SEAL / f"{board_id}.txt")
    moves = ";".join(sequence)
    out = subprocess.run(
        ["java", "-jar", str(JUDGE_SEAL), "validate", "--board", board, "--moves", moves],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_a1_onyx_card_shape_and_status_mix():
    """Eleven rounds with win/trap/fort play polarity on the card."""
    card = _load_card()
    assert "schema_tag" not in card
    rounds = card["rounds"]
    assert len(rounds) == 11
    ids = [r["board_id"] for r in rounds]
    assert ids == sorted(ids)
    assert ids == [f"board_{i:02d}" for i in range(1, 12)]
    statuses = {r["status"] for r in rounds}
    assert statuses == {"win", "trap", "fort"}
    for r in rounds:
        assert set(r) >= {
            "board_id", "status", "coop_summit", "key_move",
            "sequence", "refutations",
        }
        assert "height_delta" not in r
        if r["status"] == "win":
            assert r["coop_summit"] is True
            assert r["key_move"]
            assert r["sequence"]
            assert r["refutations"] == []
        elif r["status"] == "trap":
            assert r["coop_summit"] is True
            assert r["key_move"] == ""
            assert r["sequence"] == []
            assert isinstance(r["refutations"], list)
        else:
            assert r["status"] == "fort"
            assert r["coop_summit"] is False
            assert r["key_move"] == ""
            assert r["sequence"] == []
            assert r["refutations"] == []


def test_c3_slate_seal_and_puzzle_integrity():
    """Sealed judge and puzzle twins match live copies; card must exist."""
    assert JUDGE.is_file() and JUDGE_SEAL.is_file()
    assert JUDGE.read_bytes() == JUDGE_SEAL.read_bytes()
    live = sorted(p.name for p in PUZZLE_DIR.glob("board_*.txt"))
    sealed = sorted(p.name for p in PUZZLE_SEAL.glob("board_*.txt"))
    assert live == sealed == [f"board_{i:02d}.txt" for i in range(1, 12)]
    for name in live:
        assert (PUZZLE_DIR / name).read_bytes() == (PUZZLE_SEAL / name).read_bytes()
    # structural: card must exist (timeouts do not free-pass)
    assert CARD_PATH.is_file()


def test_e5_beryl_status_matches_independent_search():
    """Submitted status/coop_summit matches independent Santorini search."""
    card = {r["board_id"]: r for r in _load_card()["rounds"]}
    exp = _expected()
    ok = 0
    for bid, er in exp.items():
        got = card[bid]
        if got["status"] == er["status"] and bool(got["coop_summit"]) == bool(er["coop_summit"]):
            ok += 1
    assert ok >= 10, f"status/coop match {ok}/11"


def test_g2_flint_win_lines_force_against_every_reply():
    """Win sequences are judge-legal summits with forcing first moves."""
    card = {r["board_id"]: r for r in _load_card()["rounds"]}
    exp = _expected()
    wins = [bid for bid, er in exp.items() if er["status"] == "win"]
    assert len(wins) >= 3
    ok = 0
    for bid in wins:
        row = card[bid]
        if row["status"] != "win":
            continue
        data = _judge_validate(bid, row["sequence"])
        if not data.get("all_legal") or not data.get("summit"):
            continue
        # climb must be a real step onto the peak, not a padded story
        if int(data.get("height_delta", -1)) < 1:
            continue
        _, st = load_puzzle(PUZZLE_DIR / f"{bid}.txt")
        forced, _, _ = force_win(st)
        if forced and row["sequence"][0] == row["key_move"]:
            ok += 1
    assert ok >= len(wins) - 1


def test_j4_amber_trap_coop_summit_and_empty_sequence():
    """Traps keep empty sequences and true cooperative summit polarity."""
    card = {r["board_id"]: r for r in _load_card()["rounds"]}
    exp = _expected()
    traps = [bid for bid, er in exp.items() if er["status"] == "trap"]
    assert len(traps) >= 4
    ok = 0
    for bid in traps:
        row = card[bid]
        if row["status"] != "trap":
            continue
        if row["sequence"] != [] or row["key_move"] != "":
            continue
        _, st = load_puzzle(PUZZLE_DIR / f"{bid}.txt")
        coop, _, _delta = coop_summit(st)
        if coop and row["coop_summit"] is True:
            ok += 1
    assert ok >= len(traps) - 1


def test_k7_topaz_trap_refutation_coverage():
    """Trap refutations cover every graded threat (required ⊆ submitted)."""
    card = {r["board_id"]: r for r in _load_card()["rounds"]}
    exp = _expected()
    traps = [bid for bid, er in exp.items() if er["status"] == "trap"]
    ok = 0
    for bid in traps:
        row = card[bid]
        if row["status"] != "trap":
            continue
        # recompute required threat set
        _, st = load_puzzle(PUZZLE_DIR / f"{bid}.txt")
        c = classify_round(st)
        req_moves = {x["move"] for x in c["refutations"]}
        submitted = row.get("refutations") or []
        sub_moves = {x.get("move") for x in submitted if isinstance(x, dict)}
        if not req_moves.issubset(sub_moves):
            continue
        # each submitted pair must be a real answer to its threat
        good = True
        for item in submitted:
            if not isinstance(item, dict):
                good = False
                break
            mv, rp = item.get("move"), item.get("reply")
            if mv not in st.legal_moves("first") or st.first_summited(mv):
                good = False
                break
            mid = st.apply(mv)
            if rp not in mid.legal_moves("second"):
                good = False
                break
            after = mid.apply(rp)
            after.to_move = "first"
            if any(after.first_summited(t) for t in after.legal_moves("first")):
                good = False
                break
        if good:
            ok += 1
    assert ok >= len(traps) - 1


def test_m8_jade_forts_not_kiosk_cheer():
    """Forts stay fort with empty lines and no cheer verdict."""
    card = {r["board_id"]: r for r in _load_card()["rounds"]}
    exp = _expected()
    forts = [bid for bid, er in exp.items() if er["status"] == "fort"]
    assert len(forts) >= 2
    for bid in forts:
        row = card[bid]
        assert row["status"] == "fort"
        assert row["coop_summit"] is False
        assert row["sequence"] == []
        assert row["refutations"] == []


def test_n2_opal_not_kiosk_draft_verdicts():
    """Finished card must disagree with the cheerful kiosk draft on traps."""
    draft = json.loads(Path("/app/kiosk/draft_card.json").read_text())
    draft_map = {r["board_id"]: r for r in draft["rounds"]}
    card = {r["board_id"]: r for r in _load_card()["rounds"]}
    exp = _expected()
    traps = [bid for bid, er in exp.items() if er["status"] == "trap"]
    assert traps
    disagreed = 0
    for bid in traps:
        if draft_map[bid]["status"] != card[bid]["status"]:
            disagreed += 1
    assert disagreed >= 1


def test_p5_quartz_whole_booklet_and_judge_replay():
    """Whole booklet matches search; wins replay through the sealed judge."""
    card = _load_card()
    exp = _expected()
    rows = {r["board_id"]: r for r in card["rounds"]}
    matched = 0
    for bid, er in exp.items():
        got = rows[bid]
        if got["status"] != er["status"]:
            continue
        if bool(got["coop_summit"]) != bool(er["coop_summit"]):
            continue
        if got["status"] == "win":
            data = _judge_validate(bid, got["sequence"])
            if not (data.get("all_legal") and data.get("summit")):
                continue
        if got["status"] == "trap":
            req = {x["move"] for x in classify_round(load_puzzle(PUZZLE_DIR / f"{bid}.txt")[1])["refutations"]}
            sub = {x["move"] for x in got["refutations"]}
            if not req.issubset(sub):
                continue
        matched += 1
    assert matched >= 10


def test_r6_coral_emit_twice_byte_identical():
    """Kiosk refile of a finished card is byte-identical."""
    import os
    import tempfile

    card = _load_card()
    # simulate kiosk refile identity on a complete card
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "answers.json")
        with open(path, "w") as fh:
            json.dump(card, fh, indent=2, sort_keys=True)
            fh.write("\n")
        before = Path(path).read_bytes()
        env = os.environ.copy()
        env["APP_ROOT"] = "/app"
        out = subprocess.run(
            ["/app/kiosk/emit_card.sh", path],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert out.returncode == 0, out.stderr
        after = Path(path).read_bytes()
        assert before == after


def test_s3_pyrite_sensei_not_authoritative():
    """Sensei-ready traps still file as trap, not win."""
    out = subprocess.run(
        ["/app/tools/sensei_hint.sh", "/app/puzzles"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0
    reading = {}
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            reading[parts[0]] = parts[1]
    exp = _expected()
    # At least one trap must look_ready to sensei while filing as trap
    traps_ready = [
        bid for bid, er in exp.items()
        if er["status"] == "trap" and reading.get(bid) == "looks_ready"
    ]
    assert traps_ready, "sensei bait missing on traps"
    card = {r["board_id"]: r for r in _load_card()["rounds"]}
    for bid in traps_ready:
        assert card[bid]["status"] == "trap"


def test_t9_garnet_dense_trap_threat_coverage():
    """At least one dense trap keeps full threat-move coverage."""
    exp = _expected()
    dense = [bid for bid, er in exp.items() if er["status"] == "trap" and len(er["refutations"]) >= 5]
    assert dense, "expected a dense trap"
    card = {r["board_id"]: r for r in _load_card()["rounds"]}
    bid = dense[0]
    row = card[bid]
    assert row["status"] == "trap"
    req = {x["move"] for x in exp[bid]["refutations"]}
    sub = {x["move"] for x in row["refutations"]}
    assert req.issubset(sub)
