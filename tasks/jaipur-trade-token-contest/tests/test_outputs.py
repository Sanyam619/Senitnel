"""Verifier for the Jaipur trade-token booklet.

Rebuilds every verdict from the round sheets with its own house rules and
replays each filed sequence past a pristine copy of the sealed judge.
"""

from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

CARD = Path("/output/jaipur-card.json")
SHEETS = Path("/app/puzzles")
JUDGE = Path("/opt/tbench/judge.jar")
JUDGE_LIVE = Path("/app/bin/judge.jar")
VERDICTS = ("win", "trap", "fort")

GOODS = ("lea", "spi", "clo", "sil", "gol", "dia")
PRECIOUS = {"sil", "gol", "dia"}
CAM = "cam"
HAND_LIMIT = 7
BUDGET_DEFAULT = 3
SCHEMA = "jaipur-trade-v1"


@dataclass
class State:
    board_id: str = "00"
    floor: int = 10
    budget: int = BUDGET_DEFAULT
    seal: int = 5
    market: list[str] = field(default_factory=list)
    deck: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    herd: int = 0
    rival_hand: list[str] = field(default_factory=list)
    rival_herd: int = 0
    tokens: dict[str, list[int]] = field(default_factory=dict)
    bonus3: list[int] = field(default_factory=list)
    bonus4: list[int] = field(default_factory=list)
    bonus5: list[int] = field(default_factory=list)
    score: int = 0
    rival_score: int = 0
    claimed: list[str] = field(default_factory=list)  # token labels claimed by trader

    def clone(self) -> State:
        return deepcopy(self)


def parse_sheet(text: str) -> State:
    st = State()
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("board_id:"):
            st.board_id = line.split(":", 1)[1].strip()
        elif line.startswith("to_move:"):
            continue
        elif line.startswith("floor:"):
            st.floor = int(line.split(":", 1)[1].strip())
        elif line.startswith("budget:"):
            st.budget = int(line.split(":", 1)[1].strip())
        elif line.startswith("seal:"):
            st.seal = int(line.split(":", 1)[1].strip())
        elif line.startswith("market:"):
            body = line.split(":", 1)[1].strip()
            st.market = [p.strip() for p in body.split(",") if p.strip()]
        elif line.startswith("deck:"):
            body = line.split(":", 1)[1].strip()
            st.deck = [p.strip() for p in body.split(",") if p.strip()]
        elif line.startswith("hand:"):
            body = line.split(":", 1)[1].strip()
            st.hand = [p.strip() for p in body.split(",") if p.strip()]
        elif line.startswith("herd:"):
            st.herd = int(line.split(":", 1)[1].strip())
        elif line.startswith("rival_hand:"):
            body = line.split(":", 1)[1].strip()
            st.rival_hand = [p.strip() for p in body.split(",") if p.strip()]
        elif line.startswith("rival_herd:"):
            st.rival_herd = int(line.split(":", 1)[1].strip())
        elif line.startswith("bonus3:"):
            body = line.split(":", 1)[1].strip()
            st.bonus3 = [int(x) for x in body.split(",") if x.strip()]
        elif line.startswith("bonus4:"):
            body = line.split(":", 1)[1].strip()
            st.bonus4 = [int(x) for x in body.split(",") if x.strip()]
        elif line.startswith("bonus5:"):
            body = line.split(":", 1)[1].strip()
            st.bonus5 = [int(x) for x in body.split(",") if x.strip()]
        elif line == "tokens:":
            section = "tokens"
        elif section == "tokens" and ":" in line:
            g, rest = line.split(":", 1)
            st.tokens[g.strip()] = [int(x) for x in rest.split(",") if x.strip()]
    if len(st.market) != 5:
        raise ValueError(f"market must have 5 cards, got {st.market}")
    return st


def _refill(st: State) -> None:
    while len(st.market) < 5 and st.deck:
        st.market.append(st.deck.pop(0))


def _goods_count(hand: list[str], good: str) -> int:
    return sum(1 for x in hand if x == good)


def _min_sell(good: str) -> int:
    return 2 if good in PRECIOUS else 1


def _apply_sell(
    hand: list[str],
    tokens: dict[str, list[int]],
    bonus3: list[int],
    bonus4: list[int],
    bonus5: list[int],
    good: str,
    n: int,
    claim: bool,
) -> tuple[int, list[str]]:
    """Return (points, claim_labels). Mutates hand/token stacks."""
    if good not in GOODS:
        raise ValueError(f"bad good {good}")
    if n < _min_sell(good):
        raise ValueError("below min sell")
    if _goods_count(hand, good) < n:
        raise ValueError("not enough cards")
    stack = tokens.get(good, [])
    if len(stack) < n:
        raise ValueError("not enough tokens")
    pts = 0
    labels: list[str] = []
    for _ in range(n):
        hand.remove(good)
        v = stack.pop(0)
        pts += v
        if claim:
            labels.append(f"{good}:{v}")
    bonus = 0
    if n >= 5 and bonus5:
        bonus = bonus5.pop(0)
        if claim:
            labels.append(f"b5:{bonus}")
    elif n == 4 and bonus4:
        bonus = bonus4.pop(0)
        if claim:
            labels.append(f"b4:{bonus}")
    elif n == 3 and bonus3:
        bonus = bonus3.pop(0)
        if claim:
            labels.append(f"b3:{bonus}")
    pts += bonus
    return pts, labels


def apply_action(st: State, who: str, action: str) -> State:
    """Apply one legal action; raises ValueError if illegal."""
    nxt = st.clone()
    is_trader = who == "trader"
    hand = nxt.hand if is_trader else nxt.rival_hand

    if action == "herd":
        cams = [c for c in nxt.market if c == CAM]
        if not cams:
            raise ValueError("no camels in market")
        nxt.market = [c for c in nxt.market if c != CAM]
        if is_trader:
            nxt.herd += len(cams)
        else:
            nxt.rival_herd += len(cams)
        _refill(nxt)
        return nxt

    if action.startswith("take:"):
        good = action.split(":", 1)[1]
        if good == CAM:
            raise ValueError("use herd for camels")
        if good not in GOODS:
            raise ValueError("bad take")
        if good not in nxt.market:
            raise ValueError("not in market")
        if len(hand) >= HAND_LIMIT:
            raise ValueError("hand full")
        nxt.market.remove(good)
        hand.append(good)
        _refill(nxt)
        return nxt

    if action.startswith("exchange:"):
        body = action.split(":", 1)[1]
        if ">" not in body:
            raise ValueError("bad exchange")
        left, right = body.split(">", 1)
        give = [x.strip() for x in left.split(",") if x.strip()]
        take = [x.strip() for x in right.split(",") if x.strip()]
        if not give or len(give) != len(take):
            raise ValueError("exchange size")
        # Build available: hand goods + camels as 'cam' tokens from herd
        avail = list(hand)
        herd_n = nxt.herd if is_trader else nxt.rival_herd
        avail_cam = herd_n
        market_bag = list(nxt.market)
        for g in give:
            if g == CAM:
                if avail_cam <= 0:
                    raise ValueError("no camel to give")
                avail_cam -= 1
            else:
                if g not in avail:
                    raise ValueError("give missing")
                avail.remove(g)
        for t in take:
            if t not in market_bag:
                raise ValueError("take missing from market")
            market_bag.remove(t)
            if t == CAM:
                raise ValueError("cannot exchange-take camels; use herd")
        # commit
        new_hand = list(hand)
        new_herd = herd_n
        for g in give:
            if g == CAM:
                new_herd -= 1
            else:
                new_hand.remove(g)
        for t in take:
            new_hand.append(t)
            nxt.market.remove(t)
        if len([x for x in new_hand if x != CAM]) > HAND_LIMIT:
            raise ValueError("hand limit")
        # put given into market
        for g in give:
            nxt.market.append(g)
        if is_trader:
            nxt.hand = new_hand
            nxt.herd = new_herd
        else:
            nxt.rival_hand = new_hand
            nxt.rival_herd = new_herd
        # market size may exceed 5 briefly then we don't refill (exchange keeps size)
        # House: exchange swaps equal counts so market stays size 5.
        if len(nxt.market) != 5:
            raise ValueError("market size drift")
        return nxt

    if action.startswith("sell:"):
        parts = action.split(":")
        if len(parts) != 3:
            raise ValueError("bad sell")
        good, n_s = parts[1], parts[2]
        n = int(n_s)
        pts, labels = _apply_sell(
            hand,
            nxt.tokens,
            nxt.bonus3,
            nxt.bonus4,
            nxt.bonus5,
            good,
            n,
            claim=is_trader,
        )
        if is_trader:
            nxt.score += pts
            nxt.claimed.extend(labels)
            nxt.hand = hand
        else:
            nxt.rival_score += pts
            nxt.rival_hand = hand
        return nxt

    raise ValueError(f"unknown action {action}")


def finalize_seal(st: State) -> State:
    """Apply camel seal bonus at end of a filed line."""
    nxt = st.clone()
    if nxt.herd > nxt.rival_herd:
        nxt.score += nxt.seal
        nxt.claimed.append(f"seal:{nxt.seal}")
    elif nxt.rival_herd > nxt.herd:
        nxt.rival_score += nxt.seal
    return nxt


def meets_floor(st: State) -> bool:
    return finalize_seal(st).score >= st.floor


def legal_actions(st: State, who: str) -> list[str]:
    acts: list[str] = []
    is_trader = who == "trader"
    hand = st.hand if is_trader else st.rival_hand
    herd = st.herd if is_trader else st.rival_herd

    # Prefer sells, then takes, then exchanges, then herd (search witness order).
    for g in GOODS:
        cnt = _goods_count(hand, g)
        mn = _min_sell(g)
        stack = st.tokens.get(g, [])
        for n in range(mn, cnt + 1):
            if len(stack) >= n:
                acts.append(f"sell:{g}:{n}")

    if len(hand) < HAND_LIMIT:
        seen = set()
        for c in st.market:
            if c != CAM and c not in seen:
                seen.add(c)
                acts.append(f"take:{c}")

    # exchanges: size 1 only (booklet house limit keeps branching readable)
    market_goods = [c for c in st.market if c != CAM]
    give_pool: list[str] = list(hand) + [CAM] * herd
    if market_goods and give_pool:
        for ti, take_card in enumerate(market_goods):
            for gi, give_card in enumerate(give_pool):
                if give_card == take_card:
                    continue
                action = f"exchange:{give_card}>{take_card}"
                try:
                    apply_action(st, who, action)
                except ValueError:
                    continue
                if action not in acts:
                    acts.append(action)

    if any(c == CAM for c in st.market):
        acts.append("herd")
    return acts


def replay(st: State, sequence: list[str]) -> State:
    cur = st.clone()
    for step in sequence:
        who, action = step.split(" ", 1)
        cur = apply_action(cur, who, action)
    return finalize_seal(cur)


def can_coop(st: State, stones: int | None = None) -> bool:
    stones = st.budget if stones is None else stones
    if meets_floor(st):
        return True
    if stones <= 0:
        return False
    for a in legal_actions(st, "trader"):
        try:
            nxt = apply_action(st, "trader", a)
        except ValueError:
            continue
        if can_coop(nxt, stones - 1):
            return True
    return False


def can_force(st: State, stones: int | None = None) -> bool:
    stones = st.budget if stones is None else stones
    if meets_floor(st):
        return True
    if stones <= 0:
        return False
    for a in legal_actions(st, "trader"):
        try:
            after = apply_action(st, "trader", a)
        except ValueError:
            continue
        if meets_floor(after):
            return True
        if stones == 1:
            continue
        rival_moves = legal_actions(after, "rival")
        if not rival_moves:
            if can_force(after, stones - 1):
                return True
            continue
        if all(
            can_force(apply_action(after, "rival", r), stones - 1)
            for r in rival_moves
        ):
            return True
    return False


def verdict(st: State) -> str:
    force = can_force(st)
    coop = can_coop(st)
    if force:
        return "win"
    if coop:
        return "trap"
    return "fort"


def threats(st: State) -> list[str]:
    """Seal-losing first sells that threaten under soft rival replies."""
    out: list[str] = []
    for a in legal_actions(st, "trader"):
        if not a.startswith("sell:"):
            continue
        try:
            after = apply_action(st, "trader", a)
        except ValueError:
            continue
        if meets_floor(after):
            continue
        # threatens if one more trader turn under pass reaches floor
        if any(
            meets_floor(apply_action(after, "trader", a2))
            for a2 in legal_actions(after, "trader")
        ):
            out.append(a)
    return out


def find_coop_line(st: State, stones: int | None = None) -> list[str] | None:
    stones = st.budget if stones is None else stones
    if meets_floor(st):
        return []
    if stones <= 0:
        return None
    for a in legal_actions(st, "trader"):
        try:
            after = apply_action(st, "trader", a)
        except ValueError:
            continue
        step = f"trader {a}"
        if meets_floor(after):
            return [step]
        rest = find_coop_line(after, stones - 1)
        if rest is not None:
            return [step] + rest
    return None


def find_force_line(st: State, stones: int | None = None) -> list[str] | None:
    stones = st.budget if stones is None else stones
    if meets_floor(st):
        return []
    if stones <= 0:
        return None
    for a in legal_actions(st, "trader"):
        try:
            after = apply_action(st, "trader", a)
        except ValueError:
            continue
        step = f"trader {a}"
        if meets_floor(after):
            return [step]
        if stones == 1:
            continue
        rival_moves = legal_actions(after, "rival")
        if not rival_moves:
            rest = find_force_line(after, stones - 1)
            if rest is not None:
                return [step] + rest
            continue
        if all(
            can_force(apply_action(after, "rival", r), stones - 1)
            for r in rival_moves
        ):
            # pick one rival reply for the witness line
            r0 = rival_moves[0]
            mid = apply_action(after, "rival", r0)
            rest = find_force_line(mid, stones - 1)
            if rest is not None:
                return [step, f"rival {r0}"] + rest
    return None


def refutations(st: State) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for a in threats(st):
        after = apply_action(st, "trader", a)
        for r in legal_actions(after, "rival"):
            mid = apply_action(after, "rival", r)
            still = any(
                meets_floor(apply_action(mid, "trader", a2))
                for a2 in legal_actions(mid, "trader")
            )
            if not still:
                rows.append({"action": a, "reply": r})
                break
    return rows


def classify_row(st: State) -> dict[str, Any]:
    v = verdict(st)
    if v == "win":
        seq = find_force_line(st) or []
        final = replay(st, seq) if seq else finalize_seal(st)
        action = seq[0].split(" ", 1)[1] if seq else ""
        return {
            "board_id": st.board_id,
            "status": "win",
            "action": action,
            "tokens": list(final.claimed),
            "score": final.score,
            "sequence": seq,
            "refutations": [],
            "coop_seal": True,
        }
    if v == "trap":
        seq = find_coop_line(st) or []
        final = replay(st, seq) if seq else finalize_seal(st)
        action = seq[0].split(" ", 1)[1] if seq else ""
        return {
            "board_id": st.board_id,
            "status": "trap",
            "action": action,
            "tokens": list(final.claimed),
            "score": final.score,
            "sequence": seq,
            "refutations": refutations(st),
            "coop_seal": True,
        }
    return {
        "board_id": st.board_id,
        "status": "fort",
        "action": "",
        "tokens": [],
        "score": 0,
        "sequence": [],
        "refutations": [],
        "coop_seal": False,
    }

@cache
def sheets() -> dict[str, tuple]:
    out = {}
    for path in sorted(SHEETS.glob("board_*.txt")):
        st = parse_sheet(path.read_text())
        out[st.board_id] = (st, path)
    return out


def card_rounds() -> dict[str, dict]:
    data = json.loads(CARD.read_text())
    assert data.get("schema_tag") == SCHEMA
    rounds = data["rounds"]
    assert isinstance(rounds, list)
    return {str(r["board_id"]): r for r in rounds}


def judge_line(path: Path, steps: list[str]) -> dict:
    out = subprocess.run(
        [
            "java",
            "-jar",
            str(JUDGE),
            "validate",
            "--board",
            str(path),
            "--line",
            ";".join(steps),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode != 0 and not out.stdout.strip():
        raise AssertionError(out.stderr)
    return json.loads(out.stdout)


def judge_legal(path: Path, side: str) -> list[str]:
    out = subprocess.run(
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
    assert out.returncode == 0, out.stderr
    return list(json.loads(out.stdout)["actions"])


def forcing_first_moves(st: State) -> set[str]:
    moves = set()
    for a in legal_actions(st, "trader"):
        try:
            after = apply_action(st, "trader", a)
        except ValueError:
            continue
        if meets_floor(after):
            moves.add(a)
            continue
        rivals = legal_actions(after, "rival")
        if not rivals:
            if can_force(after, st.budget - 1):
                moves.add(a)
            continue
        if all(can_force(apply_action(after, "rival", r), st.budget - 1) for r in rivals):
            moves.add(a)
    return moves


def forcing_ok(st: State, sequence: list[str]) -> bool:
    if not sequence or not all(isinstance(s, str) for s in sequence):
        return False
    if not sequence[0].startswith("trader "):
        return False
    cur = st.clone()
    trader_turns = 0
    i = 0
    while i < len(sequence):
        step = sequence[i]
        who, action = step.split(" ", 1)
        if who != "trader":
            return False
        try:
            cur = apply_action(cur, "trader", action)
        except ValueError:
            return False
        trader_turns += 1
        if trader_turns > st.budget:
            return False
        if meets_floor(cur):
            return i == len(sequence) - 1
        i += 1
        remaining = st.budget - trader_turns
        rivals = legal_actions(cur, "rival")
        if rivals and not all(
            can_force(apply_action(cur, "rival", r), remaining) for r in rivals
        ):
            return False
        if i < len(sequence) and sequence[i].startswith("rival "):
            _, ract = sequence[i].split(" ", 1)
            try:
                cur = apply_action(cur, "rival", ract)
            except ValueError:
                return False
            i += 1
        elif rivals:
            return False
    return meets_floor(cur)


def friendly_ok(st: State, sequence: list[str]) -> bool:
    if not sequence:
        return False
    if any(not s.startswith("trader ") for s in sequence):
        return False
    if len(sequence) > st.budget:
        return False
    try:
        final = replay(st, sequence)
    except ValueError:
        return False
    return final.score >= st.floor


def refutations_ok(st: State, rows: list) -> bool:
    needed = set(threats(st))
    covered = set()
    for row in rows:
        if not isinstance(row, dict):
            return False
        action = row.get("action")
        reply = row.get("reply")
        if not isinstance(action, str) or not isinstance(reply, str):
            return False
        try:
            after = apply_action(st, "trader", action)
            mid = apply_action(after, "rival", reply)
        except ValueError:
            return False
        if meets_floor(after):
            return False
        still = any(
            meets_floor(apply_action(mid, "trader", a2))
            for a2 in legal_actions(mid, "trader")
        )
        if still:
            return False
        if action in needed:
            covered.add(action)
    return needed <= covered


def round_ok(board_id: str, row: dict) -> bool:
    st, path = sheets()[board_id]
    status = row.get("status")
    if status != verdict(st):
        return False
    if bool(row.get("coop_seal")) != (status != "fort"):
        return False
    sequence = row.get("sequence")
    tokens = row.get("tokens")
    score = row.get("score")
    action = row.get("action")
    refs = row.get("refutations")
    if not isinstance(sequence, list) or not isinstance(tokens, list):
        return False
    if not isinstance(score, int) or not isinstance(action, str):
        return False
    if not isinstance(refs, list):
        return False
    if status == "fort":
        return (
            sequence == []
            and action == ""
            and tokens == []
            and score == 0
            and refs == []
        )
    if status == "win":
        if refs:
            return False
        if action not in forcing_first_moves(st):
            return False
        if not forcing_ok(st, [str(s) for s in sequence]):
            return False
    elif status == "trap":
        if not friendly_ok(st, [str(s) for s in sequence]):
            return False
        if not refutations_ok(st, refs):
            return False
        if not sequence or sequence[0] != f"trader {action}":
            return False
    else:
        return False
    seen = judge_line(path, [str(s) for s in sequence])
    return (
        seen["all_legal"]
        and seen["goal_met"]
        and seen["score"] == score
        and seen["claimed"] == tokens
        and seen["trader_turns"] <= st.budget
    )


def test_a1_onyx_card_reads_as_a_tournament_card():
    """Twelve rounds, house verdict words, and empty rows only where allowed."""
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
        assert isinstance(row.get("coop_seal"), bool)
        assert isinstance(row.get("action"), str)
        assert isinstance(row.get("tokens"), list)
        assert isinstance(row.get("score"), int)
        if status == "fort":
            assert row["sequence"] == []
            assert row["action"] == ""
            assert row["tokens"] == []
            assert row["score"] == 0
        else:
            assert row["sequence"]
            assert row["action"]
            assert row["sequence"][0] == f"trader {row['action']}"
        if status != "trap":
            assert row["refutations"] == []
    filed = {row["status"] for row in rounds.values()}
    assert filed == set(VERDICTS), f"card only uses {sorted(filed)}"


def test_c3_slate_filed_sequences_replay_past_the_sealed_judge():
    """The table replays every sequence: legal actions, floor met, score match."""
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
        _, path = sheets()[board_id]
        steps = [str(s) for s in row["sequence"]]
        try:
            seen = judge_line(path, steps)
        except (AssertionError, ValueError, json.JSONDecodeError):
            continue
        if (
            seen["all_legal"]
            and seen["goal_met"]
            and seen["score"] == row.get("score")
            and seen["claimed"] == row.get("tokens")
            and seen["trader_turns"] <= BUDGET_DEFAULT
        ):
            ok += 1
    assert ok >= len(carried) - 1, f"judge accepted {ok}/{len(carried)} filed sequences"


def test_e5_beryl_verdicts_match_play_from_the_sheets():
    """Verdict words must survive an independent replay of the booklet."""
    rounds = card_rounds()
    ok = 0
    for board_id, (st, _) in sorted(sheets().items()):
        row = rounds.get(board_id, {})
        want = verdict(st)
        if row.get("status") == want and bool(row.get("coop_seal")) == (want != "fort"):
            ok += 1
    assert ok >= 11, f"verdicts agree on {ok}/12 rounds"


def test_g2_flint_forcing_sequences_really_force():
    """A win sequence has to hold up against every Rival reply, not a soft one."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (st, _) in sorted(sheets().items())
        if verdict(st) == "win"
    ]
    ok = 0
    for board_id in wanted:
        st, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "win":
            continue
        sequence = row.get("sequence")
        action = row.get("action")
        if not isinstance(sequence, list) or not isinstance(action, str):
            continue
        try:
            if action in forcing_first_moves(st) and forcing_ok(
                st, [str(s) for s in sequence]
            ):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} win sequences force the floor"


def test_j4_amber_friendly_sequences_reach_the_floor():
    """Trap sequences are Trader alone inside three actions with Rival sitting still."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (st, _) in sorted(sheets().items())
        if verdict(st) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        st, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        if row.get("status") != "trap":
            continue
        sequence = row.get("sequence")
        if not isinstance(sequence, list):
            continue
        try:
            if friendly_ok(st, [str(s) for s in sequence]):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} friendly sequences reach the floor"


def test_k7_topaz_refutations_cover_every_threat():
    """Rival must answer each seal-losing first sell, and only real answers count."""
    rounds = card_rounds()
    wanted = [
        board_id
        for board_id, (st, _) in sorted(sheets().items())
        if verdict(st) == "trap"
    ]
    ok = 0
    for board_id in wanted:
        st, _ = sheets()[board_id]
        row = rounds.get(board_id, {})
        rows = row.get("refutations")
        if row.get("status") != "trap" or not isinstance(rows, list):
            continue
        try:
            if refutations_ok(st, rows):
                ok += 1
        except (AssertionError, ValueError):
            continue
    assert ok >= len(wanted) - 1, f"{ok}/{len(wanted)} trap rounds fully refuted"


def test_m8_jade_forts_are_not_the_kiosk_cheer():
    """The kiosk stamps a win wherever a fourth action reaches; the table does not."""
    rounds = card_rounds()
    forts = [
        board_id
        for board_id, (st, _) in sorted(sheets().items())
        if verdict(st) == "fort"
    ]
    assert forts, "booklet lost its fort rounds"
    held = sum(1 for board_id in forts if rounds.get(board_id, {}).get("status") == "fort")
    assert held >= len(forts) - 1, f"{held}/{len(forts)} fort rounds filed as forts"
    optimistic = sum(1 for row in rounds.values() if row.get("status") == "win")
    assert optimistic < len(rounds), "every round filed as a win"
    for board_id in forts:
        st, _ = sheets()[board_id]
        assert not can_coop(st), f"fort {board_id} still coop-seals inside three actions"


def test_n2_coral_score_and_tokens_are_not_padded():
    """Filed score and tokens must match the sealed judge, not a padded boast."""
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
        if seen.get("score") == row.get("score") and seen.get("claimed") == row.get(
            "tokens"
        ):
            ok += 1
    assert checked >= 8
    assert ok >= checked - 1, f"score/tokens matched on {ok}/{checked} sequenced rounds"


def test_p5_quartz_whole_booklet_stands_up():
    """Near-exact booklet: verdict, play, refutations, and score together."""
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
    assert ok >= 11, f"{ok}/12 rounds stand up end to end"


def test_r6_mica_emit_twice_stays_byte_identical_on_a_finished_card(tmp_path):
    """A finished card must come out the same bytes when the desk emits twice."""
    assert CARD.is_file() and CARD.stat().st_size > 0
    body = json.loads(CARD.read_text())
    staged = tmp_path / "jaipur-card.json"
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


def test_w3_garnet_precious_goods_need_two_cards_to_sell():
    """Silver, gold, and diamond never appear as sell:GOOD:1 in the sealed legal list."""
    assert JUDGE.is_file(), "sealed judge missing"
    for board_id, (st, path) in sorted(sheets().items()):
        for side in ("trader", "rival"):
            legal = set(judge_legal(path, side))
            for token in legal:
                if token.startswith(("sell:sil:1", "sell:gol:1", "sell:dia:1")):
                    raise AssertionError(f"{board_id} {side} listed {token}")
            for token in legal_actions(st, side):
                if token.startswith("sell:"):
                    parts = token.split(":")
                    good, n = parts[1], int(parts[2])
                    assert n >= _min_sell(good)


def test_y1_opal_camel_herd_is_not_a_take():
    """Camels leave the market only through herd, never take:cam."""
    for board_id, (st, path) in sorted(sheets().items()):
        legal = set(judge_legal(path, "trader"))
        assert "take:cam" not in legal, f"{board_id} allows take:cam"
        if any(c == CAM for c in st.market):
            assert "herd" in legal, f"{board_id} missing herd with camels on the row"
