#!/usr/bin/env python3
"""Coarse mean-score spread probe used by modprobe."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path("/app/data/eval")
    spreads = []
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        scores = [float(v) for v in payload.get("token_scores", [])]
        if not scores:
            continue
        spreads.append(max(scores) - min(scores))
    if not spreads:
        print("modprobe: empty")
        return 1
    mean = sum(spreads) / len(spreads)
    print(f"modprobe: spread_ok mean={mean:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
