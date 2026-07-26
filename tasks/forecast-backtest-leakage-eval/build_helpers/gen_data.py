#!/usr/bin/env python3
"""Generate frozen series/split fixtures for forecast-backtest-leakage-eval."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "environment"
DATA = ROOT / "data"

WINDOWS = [
    {
        "id": "w_alpha",
        "seq": 1,
        "smape_causal": 0.142,
        "mase_causal": 0.880,
        "smape_leak": 0.091,
        "mase_leak": 0.550,
        "level": 100.0,
        "amp": 8.0,
        "period": 7,
        "n": 64,
        "train_end": 48,
    },
    {
        "id": "w_beta",
        "seq": 2,
        "smape_causal": 0.156,
        "mase_causal": 0.910,
        "smape_leak": 0.102,
        "mase_leak": 0.580,
        "level": 80.0,
        "amp": 6.5,
        "period": 7,
        "n": 64,
        "train_end": 48,
    },
    {
        "id": "w_gamma",
        "seq": 3,
        "smape_causal": 0.168,
        "mase_causal": 0.945,
        "smape_leak": 0.110,
        "mase_leak": 0.610,
        "level": 120.0,
        "amp": 10.0,
        "period": 7,
        "n": 72,
        "train_end": 54,
    },
    {
        "id": "w_delta",
        "seq": 4,
        "smape_causal": 0.134,
        "mase_causal": 0.860,
        "smape_leak": 0.084,
        "mase_leak": 0.520,
        "level": 90.0,
        "amp": 5.5,
        "period": 5,
        "n": 60,
        "train_end": 45,
    },
    {
        "id": "w_epsilon",
        "seq": 5,
        "smape_causal": 0.151,
        "mase_causal": 0.895,
        "smape_leak": 0.097,
        "mase_leak": 0.565,
        "level": 110.0,
        "amp": 7.0,
        "period": 7,
        "n": 70,
        "train_end": 52,
    },
]


def series_for(w: dict) -> list[float]:
    out = []
    for i in range(int(w["n"])):
        seasonal = w["amp"] * math.sin(2.0 * math.pi * i / w["period"])
        trend = 0.05 * i
        out.append(round(w["level"] + seasonal + trend, 6))
    return out


def main() -> None:
    series_dir = DATA / "series"
    splits_dir = DATA / "splits"
    reg_dir = DATA / "feature_registry"
    fixtures = DATA / "fixtures"
    ledger = DATA / "ledger"
    for d in (series_dir, splits_dir, reg_dir, fixtures, ledger):
        d.mkdir(parents=True, exist_ok=True)

    split_rows = []
    for w in WINDOWS:
        y = series_for(w)
        payload = {
            "id": w["id"],
            "seq": w["seq"],
            "period": w["period"],
            "train_end": w["train_end"],
            "smape_causal": w["smape_causal"],
            "mase_causal": w["mase_causal"],
            "smape_leak": w["smape_leak"],
            "mase_leak": w["mase_leak"],
            "y": y,
        }
        (series_dir / f"{w['id']}.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        split_rows.append(
            f"[[window]]\nid = \"{w['id']}\"\ntrain_end = {w['train_end']}\n"
            f"period = {w['period']}\n"
        )

    (splits_dir / "windows.toml").write_text("\n".join(split_rows) + "\n", encoding="utf-8")
    (splits_dir / "walk_forward.toml").write_text(
        '[policy]\nmode = "walk_forward"\norigin = "durable"\n',
        encoding="utf-8",
    )

    journal = [
        {
            "tip": "tip_g3",
            "epoch": 2,
            "sealed": True,
            "horizon": 2,
            "scaler": "train_only",
            "shift": 0.01,
        },
        {
            "tip": "tip_g7",
            "epoch": 4,
            "sealed": True,
            "horizon": 3,
            "scaler": "train_only",
            "shift": 0.0,
        },
        {
            "tip": "tip_g5",
            "epoch": 3,
            "sealed": True,
            "horizon": 3,
            "scaler": "train_only",
            "shift": 0.008,
        },
        {
            "tip": "tip_g9",
            "epoch": 7,
            "sealed": True,
            "horizon": 5,
            "scaler": "global",
            "shift": -0.045,
        },
        {
            "tip": "tip_live",
            "epoch": 9,
            "sealed": False,
            "horizon": 6,
            "scaler": "global",
            "shift": -0.06,
        },
        {
            "tip": "tip_g7",
            "epoch": 4,
            "sealed": True,
            "horizon": 3,
            "scaler": "train_only",
            "shift": 0.0,
        },
        {
            "tip": "tip_g4",
            "epoch": 1,
            "sealed": True,
            "horizon": 2,
            "scaler": "train_only",
            "shift": 0.012,
        },
        {
            "tip": "tip_live",
            "epoch": 9,
            "sealed": False,
            "horizon": 6,
            "scaler": "global",
            "shift": -0.06,
        },
    ]
    (reg_dir / "tip_journal.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in journal), encoding="utf-8"
    )
    (reg_dir / "retired_tips.jsonl").write_text(
        json.dumps({"tip": "tip_g9", "reason": "overstated_holdout"}) + "\n",
        encoding="utf-8",
    )

    # Leftover ledger bait pointing at live tip.
    (ledger / "journal.jsonl").write_text(
        json.dumps({"tip": "tip_live", "epoch": 9, "note": "all_data_mirror"}) + "\n",
        encoding="utf-8",
    )

    bait_windows = []
    for w in WINDOWS:
        bait_windows.append(
            {
                "id": w["id"],
                "smape": w["smape_leak"],
                "mase": w["mase_leak"],
                "horizon": 6,
                "split_tip": 9,
                "scaler": "global",
            }
        )
    (fixtures / "surface_ok.json").write_text(
        json.dumps(
            {
                "schema_tag": "forecast-eval-v1",
                "windows": bait_windows,
                "eval_ok": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    digest_paths = []
    for path in sorted(DATA.rglob("*")):
        if path.is_file() and path.name != "fixtures.sha256":
            rel = path.relative_to(DATA)
            digest_paths.append(path)

    lines = []
    for path in sorted(digest_paths, key=lambda p: str(p.relative_to(DATA))):
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        rel = path.relative_to(DATA).as_posix()
        lines.append(f"{h}  {rel}")
    (DATA / "fixtures.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(WINDOWS)} series + registry + digests")


if __name__ == "__main__":
    main()
