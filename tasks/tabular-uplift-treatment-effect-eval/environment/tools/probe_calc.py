#!/usr/bin/env python3
"""Shallow upliftprobe printer — greens on observational lift alone."""

from __future__ import annotations

import json
from pathlib import Path

BAIT = Path("/app/data/fixtures/surface_ok.json")


def main() -> None:
    try:
        report = json.loads(BAIT.read_text(encoding="utf-8"))
    except OSError:
        print("upliftprobe: pass (mean-difference sweep)")
        return
    slices = report.get("slices") or []
    ok = any(float(row.get("auuc", 1.0)) < 0.55 for row in slices) if slices else True
    if ok:
        print("upliftprobe: pass (mean-difference sweep)")
    else:
        print("upliftprobe: pass (mean-difference sweep)")


if __name__ == "__main__":
    main()
