#!/usr/bin/env python3
"""Handcraft and verify the twelve Onitama temple-path sheets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from engine import (
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


def pos_from(
    pieces: list[tuple[int, int, int]],
    sc: tuple[str, str],
    pc: tuple[str, str],
    sb: str,
    budget: int = 3,
) -> Pos:
    cells = empty_cells()
    for f, r, p in pieces:
        place(cells, f, r, p)
    return Pos(
        cells=tuple(cells),
        sensei_cards=sc,
        pupil_cards=pc,
        sideboard=sb,
        to_move=SENSEI,
        budget=budget,
    )


def build_booklet() -> list[tuple[str, Pos, str]]:
    """Return (board_id, pos, expected_status)."""
    sheets: list[tuple[str, Pos, str]] = []

    # --- WINS -----------------------------------------------------------------
    # 01: mate-in-1 temple via Tiger (S on c3 -> c5). Pupil master elsewhere.
    # Tiger: (0,2) and (0,-1). From c3 (2,2) + (0,2) = c5 (2,4).
    sheets.append(
        (
            "01",
            pos_from(
                [
                    (2, 2, 2),  # S on c3
                    (0, 0, 1),  # s decoy
                    (4, 4, -2),  # P tucked away on e5 (not on temple)
                    (1, 4, -1),
                ],
                ("Tiger", "Crab"),
                ("Dragon", "Frog"),
                "Rabbit",
                3,
            ),
            "win",
        )
    )

    # 02: mate-in-1 master capture via Ox from b4 onto c4? Ox: (1,0),(0,1),(0,-1)
    # S on b4 (1,3); Ox (1,0) -> c4 (2,3) where P sits.
    sheets.append(
        (
            "02",
            pos_from(
                [
                    (1, 3, 2),  # S b4
                    (2, 3, -2),  # P c4
                    (4, 0, 1),
                    (0, 4, -1),
                ],
                ("Ox", "Horse"),
                ("Crane", "Boar"),
                "Eel",
                3,
            ),
            "win",
        )
    )

    # 03: mate-in-2 force — temple after Pupil must answer a capture threat
    # S on c2; needs two Tiger/Crab steps. Simpler: S on c4 can temple with Crab (0,1)
    # only if Pupil cannot capture S first. Craft: S on b3 with Mantis to c4 then temple.
    # Use a clean force: Sensei S on c3, cards Frog+Tiger. Immediate temple with Tiger.
    # Make it mate-in-2 by blocking temple now but forcing next.
    # Position: S on d3 (3,2). Cards: Rabbit (can go e4 or c2 or ...)
    # Better crafted force:
    # Pupil P on c5 (temple). S on c3. Sensei has Boar only forward into guarded square?
    # Actually for mate-in-2: S on c2, cards Crane+Tiger. Tiger cannot reach yet (needs +2 from c2 -> c4 not temple).
    # From c2 Tiger (0,2)->c4. Then from c4 Tiger again (after rotation may lose Tiger)...
    # Start: sensei Tiger,Crab; sideboard Horse. Move1: Tiger c2-c4. Sideboard=Tiger, hand=Crab,Horse.
    # Pupil must reply. If Pupil cannot stop, Move2: need card that goes c4->c5: Crab (0,1) works.
    # Force requires every Pupil reply fails to stop. If Pupil can capture S on c4, not a force.
    # Keep Pupil pieces far so they cannot reach c4 in one move with their cards.
    sheets.append(
        (
            "03",
            pos_from(
                [
                    (2, 1, 2),  # S c2
                    (0, 0, 1),
                    (4, 4, -2),  # P e5 far
                    (0, 4, -1),
                ],
                ("Tiger", "Crab"),
                ("Monkey", "Goose"),  # poor reach toward c4 from e5
                "Horse",
                3,
            ),
            "win",
        )
    )

    # 04: mate-in-3 temple climb c1->c2->c3->c5-ish with careful cards
    # S starts c1 with Boar/Crab; climb.
    # c1 Boar (0,1)->c2; after swap get sideboard; continue.
    # Design: S on c1; Tiger,Boar; sb=Crab. 
    # Move1 Boar c1-c2; hand gets Crab. Pupil far.
    # Move2 Crab c2-c3; hand gets Boar.
    # Move3 Tiger? Tiger not in hand. After m1 sideboard=Boar, hand=Tiger,Crab.
    # After m2 use Crab: sideboard=Crab, hand=Tiger,Boar.
    # Move3 Tiger c3-c5. Yes mate-in-3.
    sheets.append(
        (
            "04",
            pos_from(
                [
                    (2, 0, 2),  # S c1
                    (4, 0, 1),
                    (0, 4, -2),
                    (4, 4, -1),
                ],
                ("Tiger", "Boar"),
                ("Eel", "Cobra"),
                "Crab",
                3,
            ),
            "win",
        )
    )

    # --- TRAPS ----------------------------------------------------------------
    # Trap pattern: Sensei can temple in 2 with Pupil sitting, but Pupil has a
    # card that captures the master or occupies temple when fighting.
    # 05: S on c3, Tiger in hand → temple if Pupil sits. Pupil on e5 with Frog/Dragon
    # that can capture S if Sensei goes to temple? Temple landing wins before reply.
    # So immediate temple is a WIN not trap. Need coop length ≥2 where first move
    # doesn't finish.
    # S on c2, Tiger+Horse, sb=Crab. Coop: Tiger c2-c4, then Crab c4-c5.
    # Fighting: after Tiger c2-c4, Pupil from nearby captures S on c4.
    # Place P on a4 with Rabbit/Ox that can reach c4? Ox from a4 (0,3): Ox (1,0)->b4, (0,1)->a5, (0,-1)->a3. No.
    # Horse from b5 (1,4): Horse (-1,0)->a5, (0,1)->b6 OOB, (0,-1)->b4. No.
    # Dragon from a5: Dragon (-2,1) OOB, (2,1)->c6 OOB, (-1,-1)->..., (1,-1)->b4.
    # Crab from a4: (2,0)->c4 YES. Pupil has Crab. Sensei uses Tiger first; sideboard becomes Tiger;
    # Pupil still has Crab in hand — can Crab a4-c4 capture S.
    sheets.append(
        (
            "05",
            pos_from(
                [
                    (2, 1, 2),  # S c2
                    (4, 0, 1),
                    (0, 3, -2),  # P a4 — Crab to c4
                    (4, 4, -1),
                ],
                ("Tiger", "Horse"),
                ("Crab", "Goose"),
                "Crab" if False else "Elephant",  # sideboard Elephant; pupil has Crab
                3,
            ),
            "trap",
        )
    )
    # fix sideboard
    sheets[-1] = (
        "05",
        pos_from(
            [
                (2, 1, 2),
                (4, 0, 1),
                (0, 3, -2),
                (4, 4, -1),
            ],
            ("Tiger", "Horse"),
            ("Crab", "Goose"),
            "Elephant",
            3,
        ),
        "trap",
    )

    # 06: similar trap with different cards — S c3 needs two-step via Boar then Ox?
    # Coop: S on d2 (3,1), cards Rabbit+Ox. Rabbit (1,1)->e3; not helpful.
    # S on c3, cards Horse+Ox (orthogonal). Coop: Horse c3-c4, Ox c4-c5.
    # Pupil P on e4 with Eel that captures c4 after first hop.
    # Eel from e4 (4,3): ( -1,1)->d4, (-1,-1)->d2, (1,0)-> OOB. No c4.
    # Cobra from e3 (4,2): (1,1) OOB, (1,-1) OOB, (-1,0)->d3. No.
    # Frog from e4: (-2,0)->c4 YES.
    sheets.append(
        (
            "06",
            pos_from(
                [
                    (2, 2, 2),  # S c3
                    (0, 0, 1),
                    (4, 3, -2),  # P e4
                    (1, 0, -1),
                ],
                ("Horse", "Ox"),
                ("Frog", "Monkey"),
                "Rooster",
                3,
            ),
            "trap",
        )
    )

    # 07: trap — capture win under coop (student takes P) but P can flee when fighting
    # S student on b3, P on c3. Sensei has Ox; student Ox (1,0) captures P.
    # That's mate-in-1 capture = WIN. Need two-step capture under coop.
    # Student on a3, cards Dragon then ... Dragon from a3 (-2,1) OOB, (2,1)->c4, etc.
    # Simpler: master capture in 2 coop plies with pupil able to step off the square.
    # P on c4. S on c2. Tiger c2-c4 captures if P stays. Fighting: P steps away with Boar.
    # After Sensei commits? If Sensei Tiger captures immediately it's win-in-1.
    # So first move must not capture: S on c1, Tiger to c3 (not onto P). P on c4.
    # Coop: Tiger c1-c3, then Boar/Crab c3-c4 capture.
    # Fighting: after Tiger c1-c3, Pupil moves P off c4 or captures S.
    sheets.append(
        (
            "07",
            pos_from(
                [
                    (2, 0, 2),  # S c1
                    (0, 0, 1),
                    (2, 3, -2),  # P c4
                    (4, 4, -1),
                ],
                ("Tiger", "Crab"),
                ("Boar", "Goose"),  # Boar from c4 can go b4/d4/c5
                "Horse",
                3,
            ),
            "trap",
        )
    )

    # 08: trap with sideboard-critical second card
    sheets.append(
        (
            "08",
            pos_from(
                [
                    (2, 1, 2),  # S c2
                    (1, 0, 1),
                    (0, 4, -2),
                    (4, 3, -1),
                ],
                ("Tiger", "Eel"),
                ("Crab", "Dragon"),  # Crab from a5? a5=(0,4); Crab (2,0)->c5 temple occupy? 
                # After Sensei Tiger c2-c4, Pupil Crab from a5 to c5 doesn't capture S.
                # Need capture of S on c4: from a5 Crab (2,0)->c5 not c4; (0,1)->a6 OOB.
                # From b5 Horse... place P on a3 with Crab to c3? 
                # Redo 08 below
                "Mantis",
                3,
            ),
            "trap",
        )
    )

    # Fix 08 properly
    sheets[-1] = (
        "08",
        pos_from(
            [
                (2, 1, 2),  # S c2
                (4, 0, 1),
                (0, 3, -2),  # P a4 with Crab -> c4 after Tiger hop
                (4, 4, -1),
            ],
            ("Tiger", "Ox"),
            ("Crab", "Rooster"),
            "Cobra",
            3,
        ),
        "trap",
    )

    # 09: trap — three-ply coop temple, pupil can interrupt
    sheets.append(
        (
            "09",
            pos_from(
                [
                    (2, 0, 2),  # S c1
                    (4, 1, 1),
                    (0, 3, -2),  # P a4
                    (4, 4, -1),
                ],
                ("Boar", "Tiger"),
                ("Crab", "Frog"),
                "Crab",  # wait duplicate name with hand — sideboard must be unique among five
                3,
            ),
            "trap",
        )
    )
    # Five cards must be distinct in Onitama. Fix sideboard.
    sheets[-1] = (
        "09",
        pos_from(
            [
                (2, 0, 2),
                (4, 1, 1),
                (0, 3, -2),
                (4, 4, -1),
            ],
            ("Boar", "Tiger"),
            ("Crab", "Frog"),
            "Elephant",
            3,
        ),
        "trap",
    )

    # --- FORTS ----------------------------------------------------------------
    # 10: S far away, budget 2, cannot reach
    sheets.append(
        (
            "10",
            pos_from(
                [
                    (0, 0, 2),  # S a1
                    (4, 0, 1),
                    (4, 4, -2),
                    (0, 4, -1),
                ],
                ("Crane", "Eel"),
                ("Dragon", "Monkey"),
                "Goose",
                2,
            ),
            "fort",
        )
    )

    # 11: temple adjacent but wrong cards (only sideways/back)
    sheets.append(
        (
            "11",
            pos_from(
                [
                    (2, 3, 2),  # S c4 — one step from temple but cards have no (0,1)
                    (0, 0, 1),
                    (0, 4, -2),
                    (4, 0, -1),
                ],
                ("Crane", "Rabbit"),  # Crane has (0,1)! Rabbit has (1,1),(2,0),(-1,-1)
                # Crane: (-1,-1),(1,-1),(0,1) — CAN temple. Bad.
                ("Mantis", "Frog"),
                "Horse",
                2,
            ),
            "fort",
        )
    )
    sheets[-1] = (
        "11",
        pos_from(
            [
                (2, 3, 2),  # S c4
                (0, 0, 1),
                (0, 4, -2),
                (4, 0, -1),
            ],
            ("Dragon", "Monkey"),  # no pure (0,1); Dragon from c4: ( -2,1)->a5, (2,1)->e5, (-1,-1)->b3, (1,-1)->d3
            ("Mantis", "Frog"),
            "Horse",
            2,
        ),
        "fort",
    )

    # 12: capture looks close but student blocks own landing / budget 1 insufficient
    sheets.append(
        (
            "12",
            pos_from(
                [
                    (1, 2, 2),  # S b3
                    (2, 2, 1),  # own student blocks c3
                    (2, 4, -2),  # P on temple c5
                    (4, 4, -1),
                ],
                ("Tiger", "Crab"),
                ("Ox", "Eel"),
                "Boar",
                1,
            ),
            "fort",
        )
    )

    return sheets


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sheets = build_booklet()
    assert len(sheets) == 12
    report = []
    ok = True
    for bid, pos, expect in sheets:
        # distinct cards
        five = list(pos.sensei_cards) + list(pos.pupil_cards) + [pos.sideboard]
        if len(set(five)) != 5:
            print(f"board {bid}: cards not distinct {five}", file=sys.stderr)
            ok = False
        row = classify(pos)
        status = row["status"]
        force = can_force(pos, pos.budget)
        coop = can_coop(pos, pos.budget)
        print(f"{bid}: expect={expect} got={status} force={force} coop={coop} mate_in={row['mate_in']}")
        if status != expect:
            print(f"  MISMATCH on {bid}", file=sys.stderr)
            ok = False
        write_sheet(OUT / f"board_{bid}.txt", bid, pos)
        report.append({"board_id": bid, **row})
    (OUT.parent / "fixtures").mkdir(exist_ok=True)
    Path("/tmp/onitama_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
