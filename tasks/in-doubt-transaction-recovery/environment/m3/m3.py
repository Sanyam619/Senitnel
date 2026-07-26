#!/usr/bin/env python3
"""Stage M3: flatten member rows per transfer."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def gather(payload: dict) -> dict:
    out = {"scenarios": {}}
    for name, bundle in payload["scenarios"].items():
        tail = {}
        for unit in bundle["units"]:
            tail[unit["id"]] = unit["state"]
        out["scenarios"][name] = {
            "mode": bundle["mode"],
            "members": bundle["members"],
            "rows": bundle["rows"],
            "actions": bundle["actions"],
            "grouped": {txid: [state] for txid, state in tail.items()},
        }
    return out


def main() -> int:
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    payload = json.loads(src.read_text(encoding="utf-8"))
    dest.write_text(json.dumps(gather(payload)) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
