"""Onitama temple-path engine — shared by generator, oracle, and local checks.

Coordinate system: files a..e (0..4), ranks 1..5 (rows 0..4). Sensei sits on
the low ranks; Pupil on the high ranks. Sensei temple is c1; Pupil temple is c5.
Card offsets are stamp-relative with +dy toward the opponent when the card
faces the mover; Pupil applies a 180° flip.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

N = 5
SENSEI, PUPIL = 0, 1
EMPTY = 0
# piece encoding: color in low bit-ish via sign; master flag
# board cells: 0 empty; +1 sensei student; +2 sensei master; -1 pupil student; -2 pupil master

CARDS: dict[str, tuple[tuple[int, int], ...]] = {
    "Tiger": ((0, 2), (0, -1)),
    "Dragon": ((-2, 1), (2, 1), (-1, -1), (1, -1)),
    "Frog": ((-2, 0), (-1, 1), (1, -1)),
    "Rabbit": ((1, 1), (2, 0), (-1, -1)),
    "Crab": ((-2, 0), (2, 0), (0, 1)),
    "Elephant": ((-1, 0), (1, 0), (-1, 1), (1, 1)),
    "Goose": ((-1, 0), (-1, 1), (1, 0), (1, -1)),
    "Rooster": ((-1, 0), (-1, -1), (1, 0), (1, 1)),
    "Monkey": ((-1, 1), (1, 1), (-1, -1), (1, -1)),
    "Mantis": ((-1, 1), (1, 1), (0, -1)),
    "Horse": ((-1, 0), (0, 1), (0, -1)),
    "Ox": ((1, 0), (0, 1), (0, -1)),
    "Crane": ((-1, -1), (1, -1), (0, 1)),
    "Boar": ((-1, 0), (1, 0), (0, 1)),
    "Eel": ((-1, 1), (-1, -1), (1, 0)),
    "Cobra": ((1, 1), (1, -1), (-1, 0)),
}

SCHEMA = "onitama-temple-v1"
BUDGET_DEFAULT = 3


def sq_name(file_i: int, rank_i: int) -> str:
    return f"{chr(ord('a') + file_i)}{rank_i + 1}"


def parse_sq(token: str) -> tuple[int, int]:
    token = token.strip().lower()
    return ord(token[0]) - ord("a"), int(token[1]) - 1


def idx(f: int, r: int) -> int:
    return r * N + f


def in_bounds(f: int, r: int) -> bool:
    return 0 <= f < N and 0 <= r < N


@dataclass(frozen=True)
class Pos:
    cells: tuple[int, ...]  # length 25
    sensei_cards: tuple[str, str]
    pupil_cards: tuple[str, str]
    sideboard: str
    to_move: int  # SENSEI or PUPIL
    budget: int

    def piece_at(self, f: int, r: int) -> int:
        return self.cells[idx(f, r)]

    def temple(self, who: int) -> tuple[int, int]:
        return (2, 0) if who == SENSEI else (2, 4)

    def master_sq(self, who: int) -> tuple[int, int] | None:
        want = 2 if who == SENSEI else -2
        for r in range(N):
            for f in range(N):
                if self.cells[idx(f, r)] == want:
                    return f, r
        return None

    def winner(self) -> int | None:
        """Return SENSEI/PUPIL if that side has already won, else None."""
        sm = self.master_sq(SENSEI)
        pm = self.master_sq(PUPIL)
        if sm is None:
            return PUPIL
        if pm is None:
            return SENSEI
        if sm == self.temple(PUPIL):
            return SENSEI
        if pm == self.temple(SENSEI):
            return PUPIL
        return None


def hand_of(pos: Pos, who: int) -> tuple[str, str]:
    return pos.sensei_cards if who == SENSEI else pos.pupil_cards


def offsets_for(card: str, who: int) -> tuple[tuple[int, int], ...]:
    raw = CARDS[card]
    if who == SENSEI:
        return raw
    return tuple((-dx, -dy) for dx, dy in raw)


def legal_moves(pos: Pos) -> list[tuple[str, int, int, int, int]]:
    """List (card, from_f, from_r, to_f, to_r) for the side to move."""
    who = pos.to_move
    if pos.winner() is not None:
        return []
    hand = hand_of(pos, who)
    own_student = 1 if who == SENSEI else -1
    own_master = 2 if who == SENSEI else -2
    moves: list[tuple[str, int, int, int, int]] = []
    for card in hand:
        for r in range(N):
            for f in range(N):
                p = pos.cells[idx(f, r)]
                if p not in (own_student, own_master):
                    continue
                for dx, dy in offsets_for(card, who):
                    tf, tr = f + dx, r + dy
                    if not in_bounds(tf, tr):
                        continue
                    dest = pos.cells[idx(tf, tr)]
                    if who == SENSEI and dest > 0:
                        continue
                    if who == PUPIL and dest < 0:
                        continue
                    moves.append((card, f, r, tf, tr))
    return moves


def apply_move(pos: Pos, move: tuple[str, int, int, int, int]) -> Pos:
    card, ff, fr, tf, tr = move
    who = pos.to_move
    cells = list(pos.cells)
    piece = cells[idx(ff, fr)]
    cells[idx(ff, fr)] = EMPTY
    cells[idx(tf, tr)] = piece
    hand = list(hand_of(pos, who))
    if card not in hand:
        raise ValueError(f"card {card} not in hand {hand}")
    hand.remove(card)
    new_side = card
    gained = pos.sideboard
    hand.append(gained)
    hand_t = (hand[0], hand[1])
    if who == SENSEI:
        sc, pc = hand_t, pos.pupil_cards
    else:
        sc, pc = pos.sensei_cards, hand_t
    return Pos(
        cells=tuple(cells),
        sensei_cards=sc,
        pupil_cards=pc,
        sideboard=new_side,
        to_move=1 - who,
        budget=pos.budget,
    )


def move_token(move: tuple[str, int, int, int, int], who: int | None = None) -> str:
    card, ff, fr, tf, tr = move
    body = f"{card}:{sq_name(ff, fr)}-{sq_name(tf, tr)}"
    if who is None:
        return body
    side = "sensei" if who == SENSEI else "pupil"
    return f"{side} {body}"


def parse_move_token(token: str) -> tuple[int, str, int, int, int, int]:
    token = token.strip()
    if " " in token:
        side_s, rest = token.split(" ", 1)
        who = SENSEI if side_s == "sensei" else PUPIL
    else:
        who = SENSEI
        rest = token
    card, path = rest.split(":", 1)
    a, b = path.split("-", 1)
    ff, fr = parse_sq(a)
    tf, tr = parse_sq(b)
    return who, card, ff, fr, tf, tr


def read_sheet(path: Path) -> Pos:
    text = path.read_text()
    meta: dict[str, str] = {}
    board_lines: list[str] = []
    mode = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("board:"):
            mode = "board"
            continue
        if mode == "board":
            board_lines.append(line.strip())
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    if len(board_lines) != N:
        raise ValueError(f"bad board rows in {path}")
    cells = [EMPTY] * (N * N)
    for r, row in enumerate(board_lines):
        if len(row) != N:
            raise ValueError(f"bad board width in {path}: {row!r}")
        for f, ch in enumerate(row):
            if ch == ".":
                continue
            if ch == "s":
                cells[idx(f, r)] = 1
            elif ch == "S":
                cells[idx(f, r)] = 2
            elif ch == "p":
                cells[idx(f, r)] = -1
            elif ch == "P":
                cells[idx(f, r)] = -2
            else:
                raise ValueError(f"bad cell {ch!r} in {path}")
    sc = tuple(x.strip() for x in meta["sensei_cards"].split(","))
    pc = tuple(x.strip() for x in meta["pupil_cards"].split(","))
    if len(sc) != 2 or len(pc) != 2:
        raise ValueError("need two cards per hand")
    to_move = SENSEI if meta.get("to_move", "sensei").lower() == "sensei" else PUPIL
    budget = int(meta.get("mate_budget", str(BUDGET_DEFAULT)))
    return Pos(
        cells=tuple(cells),
        sensei_cards=(sc[0], sc[1]),
        pupil_cards=(pc[0], pc[1]),
        sideboard=meta["sideboard"].strip(),
        to_move=to_move,
        budget=budget,
    )


def sheet_id(path: Path) -> str:
    # board_01.txt -> 01
    stem = path.stem
    return stem.split("_", 1)[1]


def key(pos: Pos) -> tuple:
    return (
        pos.cells,
        pos.sensei_cards,
        pos.pupil_cards,
        pos.sideboard,
        pos.to_move,
        pos.budget,
    )


def can_force(pos: Pos, sensei_left: int, memo: dict | None = None) -> bool:
    """Sensei to move (or about to): can Sensei force a win within sensei_left plies?"""
    if memo is None:
        memo = {}
    k = (key(pos), sensei_left, "F")
    if k in memo:
        return memo[k]
    w = pos.winner()
    if w == SENSEI:
        memo[k] = True
        return True
    if w == PUPIL:
        memo[k] = False
        return False
    if pos.to_move == SENSEI:
        if sensei_left <= 0:
            memo[k] = False
            return False
        for m in legal_moves(pos):
            nxt = apply_move(pos, m)
            if nxt.winner() == SENSEI:
                memo[k] = True
                return True
            if can_force(nxt, sensei_left - 1, memo):
                memo[k] = True
                return True
        memo[k] = False
        return False
    # Pupil to move — fighting replies
    moves = legal_moves(pos)
    if not moves:
        # forced card exchange with no piece move: swap one hand card with sideboard
        for i in range(2):
            hand = list(pos.pupil_cards)
            used = hand[i]
            hand[i] = pos.sideboard
            nxt = Pos(
                cells=pos.cells,
                sensei_cards=pos.sensei_cards,
                pupil_cards=(hand[0], hand[1]),
                sideboard=used,
                to_move=SENSEI,
                budget=pos.budget,
            )
            if not can_force(nxt, sensei_left, memo):
                memo[k] = False
                return False
        memo[k] = True
        return True
    for m in moves:
        nxt = apply_move(pos, m)
        if nxt.winner() == PUPIL:
            memo[k] = False
            return False
        if not can_force(nxt, sensei_left, memo):
            memo[k] = False
            return False
    memo[k] = True
    return True


def can_coop(pos: Pos, sensei_left: int, memo: dict | None = None) -> bool:
    """Pupil sits still (no turns). Sensei moves only; cards rotate on Sensei plies."""
    if memo is None:
        memo = {}
    # Normalize: if somehow pupil to move in coop, treat as sensei turn without pupil act
    if pos.to_move == PUPIL:
        pos = Pos(
            cells=pos.cells,
            sensei_cards=pos.sensei_cards,
            pupil_cards=pos.pupil_cards,
            sideboard=pos.sideboard,
            to_move=SENSEI,
            budget=pos.budget,
        )
    k = (key(pos), sensei_left, "C")
    if k in memo:
        return memo[k]
    w = pos.winner()
    if w == SENSEI:
        memo[k] = True
        return True
    if w == PUPIL or sensei_left <= 0:
        memo[k] = False
        return False
    for m in legal_moves(pos):
        nxt = apply_move(pos, m)
        # After Sensei move, official rules give turn to Pupil. For coop, skip Pupil
        # and restore Sensei to move while keeping the post-move card state.
        if nxt.winner() == SENSEI:
            memo[k] = True
            return True
        rest = Pos(
            cells=nxt.cells,
            sensei_cards=nxt.sensei_cards,
            pupil_cards=nxt.pupil_cards,
            sideboard=nxt.sideboard,
            to_move=SENSEI,
            budget=pos.budget,
        )
        if can_coop(rest, sensei_left - 1, memo):
            memo[k] = True
            return True
    memo[k] = False
    return False


def find_forcing_line(pos: Pos, sensei_left: int) -> list[str] | None:
    """Shortest Sensei-ply forcing line (alternates with fighting Pupil)."""

    best: list[str] | None = None
    best_sp = 10**9

    def consider(seq: list[str]) -> None:
        nonlocal best, best_sp
        sp = sensei_plies(seq, pos)
        if sp < best_sp:
            best_sp = sp
            best = seq

    def dfs(cur: Pos, left: int, acc: list[str]) -> None:
        nonlocal best
        w = cur.winner()
        if w == SENSEI:
            consider(acc)
            return
        if w == PUPIL or left <= 0:
            return
        if best is not None and sensei_plies(acc, pos) >= best_sp:
            return
        if cur.to_move == SENSEI:
            moves = legal_moves(cur)
            moves.sort(key=lambda m: 0 if apply_move(cur, m).winner() == SENSEI else 1)
            for m in moves:
                nxt = apply_move(cur, m)
                tok = move_token(m, SENSEI)
                if nxt.winner() == SENSEI:
                    consider(acc + [tok])
                    continue
                if can_force(nxt, left - 1):
                    dfs(nxt, left - 1, acc + [tok])
            return
        moves = legal_moves(cur)
        if not moves:
            # Skip sparse no-move branches — prefer positions with replies.
            return
        for m in moves:
            nxt = apply_move(cur, m)
            if nxt.winner() == PUPIL:
                continue
            if can_force(nxt, left):
                dfs(nxt, left, acc + [move_token(m, PUPIL)])
                if best is not None:
                    return

    if not can_force(pos, sensei_left):
        return None
    dfs(pos, sensei_left, [])
    return best


def find_coop_line(pos: Pos, sensei_left: int) -> list[str] | None:
    if pos.to_move == PUPIL:
        pos = Pos(
            cells=pos.cells,
            sensei_cards=pos.sensei_cards,
            pupil_cards=pos.pupil_cards,
            sideboard=pos.sideboard,
            to_move=SENSEI,
            budget=pos.budget,
        )
    best: list[str] | None = None

    def dfs(cur: Pos, left: int, acc: list[str]) -> None:
        nonlocal best
        w = cur.winner()
        if w == SENSEI:
            if best is None or len(acc) < len(best):
                best = list(acc)
            return
        if w == PUPIL or left <= 0:
            return
        if best is not None and len(acc) >= len(best):
            return
        moves = legal_moves(cur)
        moves.sort(key=lambda m: 0 if apply_move(cur, m).winner() == SENSEI else 1)
        for m in moves:
            nxt = apply_move(cur, m)
            tok = move_token(m, SENSEI)
            if nxt.winner() == SENSEI:
                dfs(nxt, left - 1, acc + [tok])
                continue
            rest_pos = Pos(
                cells=nxt.cells,
                sensei_cards=nxt.sensei_cards,
                pupil_cards=nxt.pupil_cards,
                sideboard=nxt.sideboard,
                to_move=SENSEI,
                budget=cur.budget,
            )
            dfs(rest_pos, left - 1, acc + [tok])

    if not can_coop(pos, sensei_left):
        return None
    dfs(pos, sensei_left, [])
    return best


def _apply_token(cur: Pos, tok: str, coop: bool) -> Pos:
    who, card, ff, fr, tf, tr = parse_move_token(tok)
    if coop and cur.to_move == PUPIL:
        cur = Pos(
            cells=cur.cells,
            sensei_cards=cur.sensei_cards,
            pupil_cards=cur.pupil_cards,
            sideboard=cur.sideboard,
            to_move=SENSEI,
            budget=cur.budget,
        )
    if cur.to_move != who:
        raise ValueError(f"side mismatch for {tok}: expected {cur.to_move} got {who}")
    nxt = apply_move(cur, (card, ff, fr, tf, tr))
    if coop and nxt.to_move == PUPIL and nxt.winner() is None:
        nxt = Pos(
            cells=nxt.cells,
            sensei_cards=nxt.sensei_cards,
            pupil_cards=nxt.pupil_cards,
            sideboard=nxt.sideboard,
            to_move=SENSEI,
            budget=cur.budget,
        )
    return nxt


def sideboard_trace(pos: Pos, sequence: list[str], coop: bool) -> list[str]:
    cur = pos
    out: list[str] = []
    for tok in sequence:
        cur = _apply_token(cur, tok, coop=coop)
        out.append(cur.sideboard)
        # after coop apply, sideboard is already post-Sensei
    return out


def sensei_plies(sequence: list[str], start: Pos) -> int:
    return sum(1 for tok in sequence if tok.startswith("sensei "))


def first_card(sequence: list[str]) -> str:
    if not sequence:
        return ""
    tok = sequence[0]
    # "sensei Tiger:c3-c5" -> Tiger
    body = tok.split(" ", 1)[-1]
    return body.split(":", 1)[0]


def threat_first_moves(pos: Pos) -> list[tuple[str, int, int, int, int]]:
    """Sensei first moves that don't finish now but still coop-win if Pupil sits."""
    threats = []
    if pos.to_move != SENSEI or pos.winner() is not None:
        return threats
    left = pos.budget
    for m in legal_moves(pos):
        nxt = apply_move(pos, m)
        if nxt.winner() == SENSEI:
            continue
        sit = Pos(
            cells=nxt.cells,
            sensei_cards=nxt.sensei_cards,
            pupil_cards=nxt.pupil_cards,
            sideboard=nxt.sideboard,
            to_move=SENSEI,
            budget=pos.budget,
        )
        if can_coop(sit, left - 1):
            threats.append(m)
    return threats


def refute_ok(pos: Pos, threat: tuple[str, int, int, int, int], reply_tok: str) -> bool:
    after = apply_move(pos, threat)
    if after.winner() is not None:
        return False
    if after.to_move != PUPIL:
        return False
    who, card, ff, fr, tf, tr = parse_move_token(reply_tok)
    if who != PUPIL:
        return False
    reply = (card, ff, fr, tf, tr)
    if reply not in legal_moves(after):
        return False
    nxt = apply_move(after, reply)
    if nxt.winner() == PUPIL:
        return True
    sit = Pos(
        cells=nxt.cells,
        sensei_cards=nxt.sensei_cards,
        pupil_cards=nxt.pupil_cards,
        sideboard=nxt.sideboard,
        to_move=SENSEI,
        budget=pos.budget,
    )
    return not can_coop(sit, pos.budget - 1)


def find_refutation(pos: Pos, threat: tuple[str, int, int, int, int]) -> str | None:
    after = apply_move(pos, threat)
    for m in legal_moves(after):
        tok = move_token(m, PUPIL)
        if refute_ok(pos, threat, tok):
            return tok
    return None


def classify(pos: Pos) -> dict:
    budget = pos.budget
    force = can_force(pos, budget)
    coop = can_coop(pos, budget)
    if force:
        status = "win"
    elif coop:
        status = "trap"
    else:
        status = "fort"
    row: dict = {
        "status": status,
        "coop_temple": bool(coop),
        "card_used": "",
        "mate_in": 0,
        "sequence": [],
        "sideboard": [],
        "refutations": [],
    }
    if status == "win":
        line = find_forcing_line(pos, budget)
        assert line is not None
        row["sequence"] = line
        row["card_used"] = first_card(line)
        row["mate_in"] = sensei_plies(line, pos)
        row["sideboard"] = sideboard_trace(pos, line, coop=False)
        row["refutations"] = []
    elif status == "trap":
        line = find_coop_line(pos, budget)
        assert line is not None
        row["sequence"] = line
        row["card_used"] = first_card(line)
        row["mate_in"] = len(line)
        row["sideboard"] = sideboard_trace(pos, line, coop=True)
        threats = threat_first_moves(pos)
        refs = []
        for th in threats:
            rep = find_refutation(pos, th)
            if rep is None:
                continue
            refs.append({"card": move_token(th, SENSEI), "reply": rep})
        row["refutations"] = refs
    else:
        row["sequence"] = []
        row["card_used"] = ""
        row["mate_in"] = 0
        row["sideboard"] = []
        row["refutations"] = []
    return row


def write_sheet(
    path: Path,
    board_id: str,
    pos: Pos,
) -> None:
    rows = []
    for r in range(N):
        chars = []
        for f in range(N):
            v = pos.cells[idx(f, r)]
            chars.append({0: ".", 1: "s", 2: "S", -1: "p", -2: "P"}[v])
        rows.append("".join(chars))
    body = "\n".join(
        [
            f"board_id: {board_id}",
            "to_move: sensei",
            f"mate_budget: {pos.budget}",
            f"sensei_cards: {pos.sensei_cards[0]},{pos.sensei_cards[1]}",
            f"pupil_cards: {pos.pupil_cards[0]},{pos.pupil_cards[1]}",
            f"sideboard: {pos.sideboard}",
            "board:",
            *rows,
            "",
        ]
    )
    path.write_text(body)


def empty_cells() -> list[int]:
    return [EMPTY] * (N * N)


def place(cells: list[int], f: int, r: int, piece: int) -> None:
    cells[idx(f, r)] = piece
