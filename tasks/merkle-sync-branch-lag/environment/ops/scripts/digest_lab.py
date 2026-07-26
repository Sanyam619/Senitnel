#!/usr/bin/env python3
"""Reference digest helper for leaf fixtures (uses same SHA-256 rules as syncctl)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def canonical_body(leaf_id: str, payload: str) -> str:
    return json.dumps({"id": leaf_id, "payload": payload}, separators=(",", ":"), sort_keys=True)


def leaf_digest(leaf_id: str, payload: str) -> str:
    return hashlib.sha256(canonical_body(leaf_id, payload).encode()).hexdigest()


def visible(branch: int, leaves_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(leaves_dir.glob("*.json")):
        row = json.loads(path.read_text())
        if int(row["since"]) <= branch:
            out[row["id"]] = leaf_digest(row["id"], row["payload"])
    return out


def merkle_root(leaves: dict[str, str]) -> str:
    layer = list(leaves.values())
    if not layer:
        return hashlib.sha256(b"").hexdigest()
    while len(layer) > 1:
        nxt: list[str] = []
        idx = 0
        while idx < len(layer):
            left = bytes.fromhex(layer[idx])
            right = bytes.fromhex(layer[idx + 1] if idx + 1 < len(layer) else layer[idx])
            nxt.append(hashlib.sha256(left + right).hexdigest())
            idx += 2
        layer = nxt
    return layer[0]


def main() -> None:
    branch = int(sys.argv[1])
    leaves_dir = Path("/app/data/leaves")
    leaf_map = visible(branch, leaves_dir)
    payload = {"branch": branch, "root_digest": merkle_root(leaf_map), "leaves": leaf_map}
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
