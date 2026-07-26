#!/usr/bin/env python3
"""Search for twelve Onitama sheets with the target win/trap/fort mix."""

from __future__ import annotations

import itertools
import json
import random
import sys
from pathlib import Path

from engine import (
    CARDS,
    PUPIL,
    SENSEI,
    Pos,
    can_coop,
    can_force,
    classify,
    empty_cells,
    place,
    write_sheet,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tasks/onitama-temple-path-contest/environment/puzzles"
CARD_NAMES = list(CARDS.keys())


def make_pos(
    pieces: list[tuple[int, int, int]],
    sc: tuple[str, str],
    pc: tuple[str, str],
    sb: str,
    budget: int,
) -> Pos:
    cells = empty_cells()
    for f, r, p in pieces:
        place(cells, f, r, p)
    return Pos(tuple(cells), sc, pc, sb, SENSEI, budget)


def distinct(sc, pc, sb) -> bool:
    return len({sc[0], sc[1], pc[0], pc[1], sb}) == 5


def classify_status(pos: Pos) -> str:
    force = can_force(pos, pos.budget)
    coop = can_coop(pos, pos.budget)
    if force:
        return "win"
    if coop:
        return "trap"
    return "fort"


def seed_positions() -> list[tuple[str, list, int]]:
    """Named seed geometries (pieces only) with preferred budgets."""
    return [
        # near temple
        ("near_c3", [(2, 2, 2), (0, 0, 1), (4, 4, -2), (1, 4, -1)], 3),
        ("near_c2", [(2, 1, 2), (4, 0, 1), (0, 4, -2), (4, 4, -1)], 3),
        ("near_c4", [(2, 3, 2), (0, 0, 1), (4, 4, -2), (0, 4, -1)], 2),
        ("cap_close", [(1, 3, 2), (2, 3, -2), (4, 0, 1), (0, 4, -1)], 3),
        ("climb_c1", [(2, 0, 2), (4, 0, 1), (0, 4, -2), (4, 4, -1)], 3),
        ("trap_a4", [(2, 1, 2), (4, 0, 1), (0, 3, -2), (4, 4, -1)], 3),
        ("trap_e4", [(2, 2, 2), (0, 0, 1), (4, 3, -2), (1, 0, -1)], 3),
        ("trap_c4p", [(2, 0, 2), (0, 0, 1), (2, 3, -2), (4, 4, -1)], 3),
        ("far_a1", [(0, 0, 2), (4, 0, 1), (4, 4, -2), (0, 4, -1)], 2),
        ("blocked", [(1, 2, 2), (2, 2, 1), (2, 4, -2), (4, 4, -1)], 1),
        ("edge_b2", [(1, 1, 2), (3, 0, 1), (3, 4, -2), (0, 4, -1)], 3),
        ("mid_d3", [(3, 2, 2), (0, 1, 1), (1, 4, -2), (4, 3, -1)], 3),
        ("mid_b4", [(1, 3, 2), (4, 1, 1), (3, 4, -2), (0, 2, -1)], 3),
        ("low_d1", [(3, 0, 2), (1, 0, 1), (2, 4, -2), (0, 3, -1)], 3),
        ("high_d4", [(3, 3, 2), (0, 0, 1), (0, 3, -2), (4, 4, -1)], 2),
    ]


def random_cards(rng: random.Random):
    picks = rng.sample(CARD_NAMES, 5)
    return (picks[0], picks[1]), (picks[2], picks[3]), picks[4]


def search_pool(rng: random.Random, limit: int = 4000):
    wins, traps, forts = [], [], []
    seeds = seed_positions()
    for i in range(limit):
        name, pieces, budget = seeds[i % len(seeds)]
        # jitter budget
        b = budget if i % 5 else rng.choice([1, 2, 3])
        sc, pc, sb = random_cards(rng)
        if not distinct(sc, pc, sb):
            continue
        # occasional piece jitter: swap pupil master file
        pcs = list(pieces)
        if i % 7 == 0:
            pcs = [(f, r, p) for f, r, p in pcs]
            for j, (f, r, p) in enumerate(pcs):
                if p == -2:
                    pcs[j] = (rng.randrange(5), r, p)
        # ensure masters present and not overlapping
        occupied = {}
        ok = True
        for f, r, p in pcs:
            if (f, r) in occupied:
                ok = False
                break
            occupied[(f, r)] = p
        if not ok:
            continue
        if 2 not in occupied.values() or -2 not in occupied.values():
            continue
        pos = make_pos(pcs, sc, pc, sb, b)
        st = classify_status(pos)
        row = classify(pos)
        # Prefer wins with mate_in >= 2 for hardness (keep a couple mate_in 1)
        entry = (pos, row, name)
        if st == "win":
            wins.append(entry)
        elif st == "trap":
            if row.get("_incomplete_refs"):
                continue
            if len(row["refutations"]) >= 1:
                traps.append(entry)
        else:
            forts.append(entry)
        if len(wins) >= 80 and len(traps) >= 80 and len(forts) >= 40:
            break
    return wins, traps, forts


def pick_diverse(entries, n, prefer_mate_min=None, prefer_mate_max=None):
    chosen = []
    used_cards = set()
    # sort for preference
    def score(e):
        pos, row, name = e
        m = row["mate_in"]
        s = 0
        if prefer_mate_min is not None and m >= prefer_mate_min:
            s += 10
        if prefer_mate_max is not None and m <= prefer_mate_max:
            s += 5
        s += m
        return -s

    for e in sorted(entries, key=score):
        pos, row, name = e
        sig = (pos.sensei_cards, pos.pupil_cards, pos.sideboard, pos.cells)
        if sig in used_cards:
            continue
        used_cards.add(sig)
        chosen.append(e)
        if len(chosen) >= n:
            break
    return chosen


def main() -> int:
    rng = random.Random(20260726)
    print("searching…", flush=True)
    wins, traps, forts = search_pool(rng)
    print(f"pool wins={len(wins)} traps={len(traps)} forts={len(forts)}")
    # 4 wins (prefer mate_in>=2), 5 traps, 3 forts
    deep_wins = [e for e in wins if e[1]["mate_in"] >= 2]
    if len(deep_wins) < 3:
        deep_wins = wins
    pick_w = pick_diverse(deep_wins, 4, prefer_mate_min=2)
    # ensure at least one mate_in 1 if available for variety
    short = [e for e in wins if e[1]["mate_in"] == 1]
    if short and pick_w and pick_w[0][1]["mate_in"] != 1:
        pick_w[0] = short[0]
    pick_t = pick_diverse(traps, 5, prefer_mate_min=2)
    pick_f = pick_diverse(forts, 3)
    if len(pick_w) < 4 or len(pick_t) < 5 or len(pick_f) < 3:
        print("insufficient pool", file=sys.stderr)
        return 1
    booklet = pick_w + pick_t + pick_f
    # Stable order: wins, traps, forts already; assign ids 01..12
    OUT.mkdir(parents=True, exist_ok=True)
    report = []
    for i, (pos, row, name) in enumerate(booklet, start=1):
        bid = f"{i:02d}"
        write_sheet(OUT / f"board_{bid}.txt", bid, pos)
        full = {"board_id": bid, "seed": name, **row}
        report.append(full)
        print(
            f"{bid} {row['status']} mate_in={row['mate_in']} "
            f"coop={row['coop_temple']} refs={len(row['refutations'])} seed={name}"
        )
    Path("/tmp/onitama_report.json").write_text(json.dumps(report, indent=2) + "\n")
    # sanity: counts
    from collections import Counter

    c = Counter(r["status"] for r in report)
    print("counts", dict(c))
    assert c["win"] == 4 and c["trap"] == 5 and c["fort"] == 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
