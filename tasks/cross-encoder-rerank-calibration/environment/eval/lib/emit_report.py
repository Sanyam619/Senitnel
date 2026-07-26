#!/usr/bin/env python3
"""Publish /output/rerank-eval.json from frozen pools, packs, and tip materials."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

APP = Path("/app")
EVAL_ROOT = Path(__file__).resolve().parents[1]
for p in (str(APP), str(EVAL_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from bevel import facet, knot, lens, weave

from lib.common import (
    agree,
    fold_all,
    hits_at,
    read_blob,
    read_dir_lots,
    read_marks,
    read_tags,
)


def app_root() -> Path:
    env = os.environ.get("BEVEL_ROOT", "").strip()
    return Path(env) if env else Path("/app")


def empty_lot(name: str):
    from lib.common import Lot

    return Lot(name=name, tags=[], lw=[], rows=[])


def compute():
    root = app_root() / "data"
    marks = read_marks(root / "feature_registry" / "tip_journal.jsonl")
    retired = knot.read_retired(root / "feature_registry" / "retired_tips.jsonl")
    idx = knot.knot_r(marks, retired)
    temperature, fusion = facet.facet_q(idx, root)
    tau = temperature
    lots_a = read_dir_lots(root / "pools" / "pool_a", "pool_a")
    lots_b = read_dir_lots(root / "pools" / "pool_b", "pool_b")
    all_lots = list(lots_a) + list(lots_b)
    fam_a = fold_all(lots_a, "a")
    fam_b = fold_all(lots_b, "b")
    mixed = weave.weave_m(marks, all_lots, retired)
    if len(mixed) == 2:
        mix_c, mix_d = mixed[0], mixed[1]
    else:
        mix_c, mix_d = empty_lot("c"), empty_lot("d")

    def load(name: str) -> bytes:
        return read_blob(root / "packs" / name)

    plan = [
        ("cold_a", load("cold_a.ckpt"), fam_a),
        ("resume_a", load("resume_a.ckpt"), fam_a),
        ("cold_b", load("cold_b.ckpt"), fam_b),
        ("resume_b", load("resume_b.ckpt"), fam_b),
        ("mix_c", load("resume_a.ckpt"), mix_c),
        ("mix_d", load("resume_b.ckpt"), mix_d),
    ]
    cells = []
    for cid, blob, lot in plan:
        qs = lens.lens_unfold(blob)
        qt = read_tags(blob)
        hits = hits_at(qs, qt, lot, tau, 10)
        nq = len(qs)
        ndcg = (hits / nq) if nq else 0.0
        mrr = agree(qs, qt, lot, tau)
        cells.append(
            {
                "id": cid,
                "ndcg": ndcg,
                "mrr": mrr,
            }
        )
    return {
        "idx": idx,
        "temperature": temperature,
        "fusion": fusion,
        "cells": cells,
    }


def read_bands(path: Path) -> dict[str, tuple[float, float, float, float]]:
    out: dict[str, tuple[float, float, float, float]] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 5:
            continue
        try:
            vals = [float(cols[i]) for i in range(1, 5)]
        except ValueError:
            continue
        out[cols[0]] = (vals[0], vals[1], vals[2], vals[3])
    return out


def temp_band(path: Path) -> tuple[float, float]:
    if not path.is_file():
        return 0.118, 0.131
    for line in path.read_text(encoding="utf-8").splitlines():
        key = "Temperature band is "
        idx = line.find(key)
        if idx < 0:
            continue
        rest = line[idx + len(key) :]
        for sep in ("–", "-"):
            if sep in rest:
                parts = [p.strip() for p in rest.split(sep, 1)]
                if len(parts) >= 2:
                    hi = "".join(ch for ch in parts[1] if ch.isdigit() or ch == ".")
                    try:
                        return float(parts[0]), float(hi)
                    except ValueError:
                        pass
    return 0.118, 0.131


def fmt6(v: float) -> str:
    return f"{v:.6f}"


def run_eval(out_path: Path | None) -> None:
    board = compute()
    bands_path = app_root() / "docs" / "rerank_bands.md"
    bands = read_bands(bands_path)
    t_lo, t_hi = temp_band(bands_path)
    ok = bool(board["cells"])
    temp = float(board["temperature"])
    if not (t_lo <= temp <= t_hi):
        ok = False
    for c in board["cells"]:
        b = bands.get(c["id"])
        if b is None:
            ok = False
            continue
        n_lo, n_hi, m_lo, m_hi = b
        if not (n_lo <= c["ndcg"] <= n_hi and m_lo <= c["mrr"] <= m_hi):
            ok = False
    parts = ['{"schema_tag":"rerank-eval-v1","slices":[']
    for i, c in enumerate(board["cells"]):
        if i:
            parts.append(",")
        parts.append(
            "{"
            f"\"id\":\"{c['id']}\","
            f"\"ndcg_at_10\":{fmt6(c['ndcg'])},"
            f"\"mrr\":{fmt6(c['mrr'])},"
            f"\"temperature\":{fmt6(temp)},"
            f"\"fusion\":\"{board['fusion']}\","
            f"\"tip_epoch\":{board['idx']}"
            "}"
        )
    parts.append('],"eval_ok":')
    parts.append("true" if ok else "false")
    parts.append("}\n")
    body = "".join(parts)
    if out_path is None:
        sys.stdout.write(body)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    run_eval(args.out)


if __name__ == "__main__":
    main()
