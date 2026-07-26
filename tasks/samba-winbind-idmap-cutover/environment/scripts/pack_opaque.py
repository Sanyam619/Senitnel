#!/usr/bin/env python3
"""Pack opaque tip/journal binaries at image materialize time."""
from __future__ import annotations

import struct
import sys
from pathlib import Path


def pack_tips(path: Path) -> None:
    rows = [
        {"kn": "rid", "lo": 30000, "hi": 39999, "rk": 8, "gen": 17, "tag": ""},
        {"kn": "autorid", "lo": 10000, "hi": 19999, "rk": 8, "gen": 17, "tag": ""},
        {
            "kn": "hash",
            "lo": 90000,
            "hi": 99999,
            "rk": 12,
            "gen": 17,
            "tag": "S-1-5-21-9999-8888-7777-1",
        },
        {"kn": "autorid", "lo": 10000, "hi": 19999, "rk": 9, "gen": 30, "tag": ""},
        # Novel equal-rk later tip selected only with later-wins under seal fence.
        {"kn": "autorid", "lo": 10000, "hi": 19999, "rk": 8, "gen": 17, "tag": ""},
    ]
    body = bytearray()
    body += b"TIP2"
    body += struct.pack(">I", len(rows))
    for r in rows:
        tag = r.get("tag") or ""
        flags = 1 if tag else 0
        kn = r["kn"].encode()
        body += struct.pack(">HBB", int(r["gen"]), int(r["rk"]), flags)
        body += struct.pack(">B", len(kn)) + kn
        body += struct.pack(">II", int(r["lo"]), int(r["hi"]))
        if flags:
            tb = tag.encode()
            body += struct.pack(">B", len(tb)) + tb
    path.write_bytes(bytes(body))


def pack_journal(path: Path) -> None:
    rows = [
        {"kind": 1, "mode": 1, "gen": 17, "hold": "lab-tmp"},
        {"kind": 2, "mode": 2, "gen": 17, "hold": "wb-hold-17"},
        {"kind": 1, "mode": 1, "gen": 18, "hold": "lab-tmp"},
        {"kind": 2, "mode": 2, "gen": 16, "hold": "wb-hold-16"},
        {"kind": 1, "mode": 1, "gen": 17, "hold": "lab-tmp"},
    ]
    body = bytearray()
    body += b"JRN2"
    body += struct.pack(">I", len(rows))
    for r in rows:
        hold = r["hold"].encode()
        body += struct.pack(">BBH", int(r["kind"]), int(r["mode"]), int(r["gen"]))
        body += struct.pack(">B", len(hold)) + hold
    path.write_bytes(bytes(body))


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/lib/samba")
    (root / "journal").mkdir(parents=True, exist_ok=True)
    (root / "ops").mkdir(parents=True, exist_ok=True)
    pack_tips(root / "journal" / "tips.bin")
    pack_journal(root / "ops" / "journal.bin")
    print("packed", root / "journal/tips.bin", root / "ops/journal.bin")


if __name__ == "__main__":
    main()
