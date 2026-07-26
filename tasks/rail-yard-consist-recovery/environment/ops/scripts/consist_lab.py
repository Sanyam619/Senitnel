#!/usr/bin/env python3
"""Reference probe helper for movement fixtures (uses same SHA-256 rules as yardctl)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def apply_movement(tracks: dict[str, list[str]], row: dict) -> None:
    track = row["track"]
    car = row["car"]
    tracks.setdefault(track, [])
    if row["op"] == "place":
        pos = int(row["pos"])
        tracks[track] = [c for c in tracks[track] if c != car]
        pos = max(0, min(pos, len(tracks[track])))
        tracks[track].insert(pos, car)
    elif row["op"] == "pull":
        tracks[track] = [c for c in tracks[track] if c != car]


def consist_at(seq: int, events_dir: Path) -> dict[str, list[str]]:
    tracks: dict[str, list[str]] = {}
    rows = []
    for path in sorted(events_dir.glob("evt_*.json")):
        rows.append(json.loads(path.read_text()))
    rows.sort(key=lambda r: int(r["seq"]))
    for row in rows:
        if int(row["seq"]) > seq:
            break
        apply_movement(tracks, row)
    return {k: tracks[k][:] for k in sorted(tracks)}


def audit_digest(tracks: dict[str, list[str]]) -> str:
    body = json.dumps(tracks, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def main() -> None:
    seq = int(sys.argv[1])
    events_dir = Path("/app/data/events")
    tracks = consist_at(seq, events_dir)
    payload = {"replay_seq": seq, "tracks": tracks, "audit_digest": audit_digest(tracks)}
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
