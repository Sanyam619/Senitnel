"""Board hunt: classify one Abalone sheet and build its card row."""

from __future__ import annotations

from pathlib import Path

from board_hunt.engine import (
    BLACK,
    apply_move,
    find_coop_line,
    find_force_line,
    find_refutation,
    fmt_move,
    forcing_first_moves,
    parse_board,
    parse_move_on,
    threats,
    verdict,
)


def _replay_ejected(cells, sequence: list[str]) -> int:
    cur = cells
    total = 0
    for step in sequence:
        colour, mv = step.split(" ", 1)
        who = BLACK if colour == "black" else 2
        parsed = parse_move_on(cur, mv, who)
        cur, ej = apply_move(cur, parsed, who)
        total += ej
    return total


def op_b(sheet: Path) -> dict:
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

    if status == "fort":
        return {
            "board_id": board_id,
            "status": "fort",
            "key_push": "",
            "ejected": 0,
            "sequence": [],
            "refutations": [],
            "coop_eject": False,
        }

    if status == "win":
        sequence = find_force_line(cells)
        if not sequence:
            raise RuntimeError(f"no forcing line on {board_id}")
        best = sequence[0].split(" ", 1)[1]
        forced_heads = forcing_first_moves(cells)
        if best not in forced_heads:
            raise RuntimeError(f"PV head not forcing on {board_id}: {best}")
        return {
            "board_id": board_id,
            "status": "win",
            "key_push": best,
            "ejected": _replay_ejected(cells, sequence),
            "sequence": sequence,
            "refutations": [],
            "coop_eject": True,
        }

    line = find_coop_line(cells)
    if not line:
        raise RuntimeError(f"no friendly line on {board_id}")
    best = line[0].split(" ", 1)[1]
    refs = []
    for threat in threats(cells):
        reply = find_refutation(cells, threat)
        if reply is None:
            raise RuntimeError(f"unrefuted threat on {board_id}: {fmt_move(threat)}")
        refs.append({"move": fmt_move(threat), "reply": reply})
    refs.sort(key=lambda r: r["move"])
    return {
        "board_id": board_id,
        "status": "trap",
        "key_push": best,
        "ejected": _replay_ejected(cells, line),
        "sequence": line,
        "refutations": refs,
        "coop_eject": True,
    }
