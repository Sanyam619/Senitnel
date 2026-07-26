#!/usr/bin/env python3
"""Stage R9: emit transfer decisions."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def pick(coord, fragments, mode, member_count):
    if coord is not None:
        return coord
    prepared = 0
    for value in fragments:
        state = value.split(":", 1)[-1]
        if state == "ABORTED":
            return "ABORT"
        if state == "PREPARED":
            prepared += 1
    if prepared >= member_count:
        return "COMMIT"
    return "ABORT"


def weave(payload: dict) -> dict:
    out = {"scenarios": {}}
    for name, bundle in payload["scenarios"].items():
        ids = set(bundle["rows"]) | set(bundle["grouped"])
        decisions = {}
        for txid in sorted(ids):
            decisions[txid] = pick(
                bundle["rows"].get(txid),
                bundle["grouped"].get(txid, []),
                bundle["mode"],
                len(bundle["members"]),
            )
        out["scenarios"][name] = {
            "actions": bundle["actions"],
            "decisions": decisions,
        }
    return out


def main() -> int:
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    payload = json.loads(src.read_text(encoding="utf-8"))
    dest.write_text(json.dumps(weave(payload)) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
