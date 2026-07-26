"""Board hunt: classify one Carcassonne sheet into a card row."""

from __future__ import annotations

from pathlib import Path

from board_hunt.engine import (
    board_id_of,
    find_coop_line,
    find_force_line,
    find_refutation,
    parse_red_move,
    parse_sheet,
    threats,
    verdict,
)


def _score_delta(sequence: list[str], sheet_text: str) -> int:
    from board_hunt.engine import apply_blue, apply_red
    from board_hunt.engine import parse_sheet as ps

    st = ps(sheet_text)
    for step in sequence:
        colour, move = step.split(" ", 1)
        if colour == "red":
            st = apply_red(st, move)
        else:
            st = apply_blue(st, move)
    return st.score


def op_b(sheet: Path) -> dict:
    text = sheet.read_text()
    st = parse_sheet(text)
    board_id = board_id_of(text, sheet.stem)

    status = verdict(st)

    if status == "fort":
        return {
            "board_id": board_id,
            "status": "fort",
            "tile": "",
            "meeple": "",
            "score_delta": 0,
            "sequence": [],
            "refutations": [],
            "coop_claim": False,
        }

    if status == "win":
        sequence = find_force_line(st)
        if not sequence:
            raise RuntimeError(f"no forcing line on {board_id}")
        first = sequence[0].split(" ", 1)[1]
        _code, _cell, _rot, meeple = parse_red_move(first)
        tile = first.split("+", 1)[0]
        seat = "" if meeple is None else f"{meeple.kind}:{meeple.edge}"
        return {
            "board_id": board_id,
            "status": "win",
            "tile": tile,
            "meeple": seat,
            "score_delta": _score_delta(sequence, text),
            "sequence": sequence,
            "refutations": [],
            "coop_claim": True,
        }

    line = find_coop_line(st)
    if not line:
        raise RuntimeError(f"no friendly line on {board_id}")
    first = line[0].split(" ", 1)[1]
    _code, _cell, _rot, meeple = parse_red_move(first)
    tile = first.split("+", 1)[0]
    seat = "" if meeple is None else f"{meeple.kind}:{meeple.edge}"
    refs = []
    for threat in threats(st):
        reply = find_refutation(st, threat)
        if reply is None:
            raise RuntimeError(f"unrefuted threat on {board_id}: {threat}")
        refs.append({"placement": threat, "reply": reply})
    refs.sort(key=lambda r: r["placement"])
    return {
        "board_id": board_id,
        "status": "trap",
        "tile": tile,
        "meeple": seat,
        "score_delta": _score_delta(line, text),
        "sequence": line,
        "refutations": refs,
        "coop_claim": True,
    }
