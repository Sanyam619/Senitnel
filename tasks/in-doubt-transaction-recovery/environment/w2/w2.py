#!/usr/bin/env python3
"""Stage W2: emit saga cleanup lists."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def arrange(payload: dict) -> dict:
    out = {"scenarios": {}}
    for name, bundle in payload["scenarios"].items():
        by_group = defaultdict(list)
        for action in bundle["actions"]:
            by_group[action["group"]].append(action)
        sagas = {}
        for group, steps in by_group.items():
            labels = []
            for action in steps:
                if bundle["decisions"].get(group) == "COMMIT":
                    continue
                if action["state"] != "PENDING":
                    labels.append(action["label"])
            sagas[group] = labels
        out["scenarios"][name] = {
            "decisions": bundle["decisions"],
            "sagas": sagas,
        }
    return out


def main() -> int:
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    payload = json.loads(src.read_text(encoding="utf-8"))
    dest.write_text(json.dumps(arrange(payload)) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
