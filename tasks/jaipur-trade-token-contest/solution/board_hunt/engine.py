"""Jaipur market engine — shared prototype for puzzle design / oracle / verifier."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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


if __name__ == "__main__":
    import json
    import sys

    p = Path(sys.argv[1])
    st = parse_sheet(p.read_text())
    print(json.dumps(classify_row(st), indent=2))
