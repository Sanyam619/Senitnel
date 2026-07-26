#!/bin/bash
set -euo pipefail

cat > /app/calib/trial_pref.toml <<'EOF'
# Evaluation selection for the cross-encoder rerank desk.

[evaluation]
selection = "serving"
refresh = "auto"

[desk]
owner = "rerank-eval-rotation"
window = "weekly"
EOF

printf 'tip_g7\n' > /app/calib/tip_bind.accept

cat > /app/bevel/lens.py <<'EOF'
"""Score-pack unfold for cold/resume frames."""

from __future__ import annotations

import struct


def _rd_u32(b: bytes, off: list[int]) -> int:
    v = struct.unpack_from("<I", b, off[0])[0]
    off[0] += 4
    return v


def _rd_f32(b: bytes, off: list[int]) -> float:
    v = struct.unpack_from("<f", b, off[0])[0]
    off[0] += 4
    return float(v)


def _rd_rowf(b: bytes, off: list[int], dim: int) -> list[float]:
    row = []
    for _ in range(dim):
        row.append(_rd_f32(b, off))
    return row


def _scale_row(row: list[float], coef: float) -> list[float]:
    scaled = []
    for v in row:
        scaled.append(v * coef)
    return scaled


def lens_unfold(blob: bytes) -> list[list[float]]:
    if len(blob) < 12:
        return []
    magic = blob[0:4]
    off = [4]
    n = _rd_u32(blob, off)
    dim = _rd_u32(blob, off)
    if magic == b"CKP1":
        off[0] += 2 * n
        out = []
        for _ in range(n):
            out.append(_rd_rowf(blob, off, dim))
        return out
    if magic == b"CKP2":
        block = _rd_u32(blob, off)
        off[0] += 2 * n
        out: list[list[float]] = []
        done = 0
        while done < n and block > 0:
            coef = _rd_f32(blob, off)
            take = min(block, n - done)
            for _ in range(take):
                row = _rd_rowf(blob, off, dim)
                out.append(_scale_row(row, coef))
            done += take
        return out
    return []
EOF

cat > /app/bevel/knot.py <<'EOF'
"""Tip generation pick for the rerank desk."""

from __future__ import annotations

from pathlib import Path


def read_retired(path: Path) -> set[str]:
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


def knot_r(marks, retired: set[str]) -> int:
    eligible = [
        m.idx
        for m in marks
        if m.state == "durable" and m.tip not in retired
    ]
    if not eligible:
        return 0
    return max(eligible)
EOF

cat > /app/bevel/facet.py <<'EOF'
"""Temperature / fusion schedule row for a tip generation."""

from __future__ import annotations

from pathlib import Path


def facet_q(idx: int, root: Path) -> tuple[float, str]:
    from lib.common import read_marks

    marks = read_marks(root / "feature_registry" / "tip_journal.jsonl")
    fam = ""
    for m in marks:
        if m.idx == idx:
            fam = m.sheet
            break
    table = root / "sched" / f"table_{fam}.toml"
    return _row_of(table, idx)


def _row_of(path: Path, idx: int) -> tuple[float, str]:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    key = f'"{idx}"'
    temperature = 0.0
    fusion = ""
    section = ""
    for line in text.splitlines():
        line = line.strip()
        if line == "[temperature]":
            section = "temperature"
            continue
        if line == "[fusion]":
            section = "fusion"
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
                elif section == "fusion":
                    fusion = rest.strip('"')
    return temperature, fusion
EOF

cat > /app/bevel/weave.py <<'EOF'
"""Mixed-slice candidate pool composition."""

from __future__ import annotations


def weave_m(marks, lots, retired: set[str]):
    from lib.common import fold_all

    tip = None
    for m in marks:
        if m.state == "durable" and m.tip not in retired and m.weft_c:
            if tip is None or m.idx > tip.idx:
                tip = m
    if tip is None:
        return []

    def pick(names, label):
        sel = [lot for n in names for lot in lots if lot.name == n]
        return fold_all(sel, label)

    return [pick(tip.weft_c, "c"), pick(tip.weft_d, "d")]
EOF

/app/scripts/run_rerank_eval.sh

head -c 200 /output/rerank-eval.json || true
echo
