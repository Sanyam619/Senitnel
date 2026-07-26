"""Classify one Onitama sheet into a tournament card row."""

from __future__ import annotations

from pathlib import Path

from board_hunt.engine import classify, read_sheet, sheet_id


def op_b(sheet: Path, schema_tag: str) -> dict:
    _ = schema_tag
    pos = read_sheet(sheet)
    info = classify(pos)
    info.pop("_incomplete_refs", None)
    return {
        "board_id": sheet_id(sheet),
        "status": info["status"],
        "card_used": info["card_used"],
        "mate_in": info["mate_in"],
        "sequence": info["sequence"],
        "sideboard": info["sideboard"],
        "refutations": info["refutations"],
        "coop_temple": info["coop_temple"],
    }
