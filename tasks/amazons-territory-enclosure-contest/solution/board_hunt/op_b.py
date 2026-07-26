"""Board hunt: classify one Amazons sheet and build its card row."""

from __future__ import annotations

from pathlib import Path

from board_hunt.engine import (
    BUDGET,
    WHITE,
    apply_turn,
    can_coop,
    find_coop_line,
    find_force_line,
    find_refutation,
    fmt_move,
    forcing_first_moves,
    parse_board,
    parse_move,
    territory,
    threats,
    verdict,
)


def _replay_delta(cells, sequence: list[str]) -> int:
    cur = cells
    for step in sequence:
        colour, mv = step.split(" ", 1)
        who = WHITE if colour == "white" else 2
        cur = apply_turn(cur, parse_move(mv), who)
    return territory(cur)[2]


def op_b(sheet: Path, schema_tag: str) -> dict:
    del schema_tag
    text = sheet.read_text()
    cells = parse_board(text)
    board_id = ""
    for line in text.splitlines():
        if line.startswith("board_id:"):
            board_id = line.split(":", 1)[1].strip()
            break
    if not board_id:
        board_id = sheet.stem.replace("board_", "")

    status = verdict(cells)
    coop = bool(can_coop(cells, BUDGET))

    if status == "fort":
        return {
            "board_id": board_id,
            "status": "fort",
            "best_move": "",
            "territory_delta": 0,
            "sequence": [],
            "refutations": [],
            "coop_enclose": False,
        }

    if status == "win":
        sequence = find_force_line(cells)
        if not sequence:
            raise RuntimeError(f"no forcing line on {board_id}")
        best = sequence[0].split(" ", 1)[1]
        forced_heads = {fmt_move(t) for t in forcing_first_moves(cells)}
        if best not in forced_heads:
            raise RuntimeError(f"PV head not forcing on {board_id}: {best}")
        return {
            "board_id": board_id,
            "status": "win",
            "best_move": best,
            "territory_delta": _replay_delta(cells, sequence),
            "sequence": sequence,
            "refutations": [],
            "coop_enclose": True,
        }

    line = find_coop_line(cells)
    if not line:
        raise RuntimeError(f"no friendly line on {board_id}")
    sequence = [f"white {fmt_move(t)}" for t in line]
    refs = []
    for th in threats(cells):
        reply = find_refutation(cells, th)
        if reply is None:
            raise RuntimeError(f"unanswered threat on {board_id}: {fmt_move(th)}")
        refs.append({"move": fmt_move(th), "reply": fmt_move(reply)})
    return {
        "board_id": board_id,
        "status": "trap",
        "best_move": fmt_move(line[0]),
        "territory_delta": _replay_delta(cells, sequence),
        "sequence": sequence,
        "refutations": refs,
        "coop_enclose": coop,
    }
