"""Logit-scale / negative-pool schedule row for a tip generation."""

from __future__ import annotations

from pathlib import Path


def facet_q(idx: int, root: Path) -> tuple[float, str]:
    from lib.common import read_marks

    marks = read_marks(root / "feature_registry" / "tip_journal.jsonl")
    fam = ""
    if marks:
        fam = max(marks, key=lambda m: m.idx).sheet
    table = root / "sched" / f"table_{fam}.toml"
    return _row_of(table, idx)


def _row_of(path: Path, idx: int) -> tuple[float, str]:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    key = f'"{idx}"'
    temperature = 0.0
    pool = ""
    section = ""
    for line in text.splitlines():
        line = line.strip()
        if line == "[temperature]":
            section = "temperature"
            continue
        if line == "[pool]":
            section = "pool"
            continue
        if line.startswith(key):
            rest = line[len(key) :].lstrip()
            if rest.startswith("="):
                rest = rest[1:].strip()
                if section == "temperature":
                    try:
                        temperature = float(rest)
                    except ValueError:
                        pass
                elif section == "pool":
                    pool = rest.strip('"')
    return temperature, pool
