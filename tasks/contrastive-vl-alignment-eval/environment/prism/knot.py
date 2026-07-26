"""Tip generation pick for the VL desk."""

from __future__ import annotations

from pathlib import Path


def skim_x(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    out: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        i = line.find('"tip"')
        if i < 0:
            continue
        rest = line[i + 5 :].lstrip().lstrip(":").lstrip()
        if not rest.startswith('"'):
            continue
        rest = rest[1:]
        end = rest.find('"')
        if end >= 0:
            out.add(rest[:end])
    return out


def knot_r(marks, _retired: set[str]) -> int:
    top = 0
    for m in marks:
        top = max(top, m.idx)
    return top
