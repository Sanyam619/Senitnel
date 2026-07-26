#!/usr/bin/env python3
"""Print max and min tier heads for movement journals."""

from __future__ import annotations

import json
from pathlib import Path


def tier_head(path: Path) -> int:
    head = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        head = max(head, int(rec["seq"]))
    return head


def main() -> None:
    root = Path("/app/data/movements")
    heads = {p.stem.replace("tier_", ""): tier_head(p) for p in sorted(root.glob("tier_*.jsonl"))}
    print(json.dumps(heads, sort_keys=True))


if __name__ == "__main__":
    main()
