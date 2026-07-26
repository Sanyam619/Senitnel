"""Classify one sheet into a card row."""
from __future__ import annotations

from pathlib import Path

from board_hunt.engine import classify_row, parse_sheet


def op_b(sheet: Path, schema_tag: str) -> dict:
    if schema_tag != "jaipur-trade-v1":
        raise ValueError("unexpected schema")
    st = parse_sheet(sheet.read_text())
    return classify_row(st)
