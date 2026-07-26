#!/usr/bin/env python3
"""Shared consist aggregation helpers for lane/yardctl."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


DATA = Path("/app/data")
CFG = Path("/app/config/l7")


def _toml_field(name: str):
    for path in sorted(CFG.glob("*.toml")):
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped.startswith(f"{name} ="):
                continue
            raw = stripped.split("=", 1)[1].strip()
            if raw.startswith('"'):
                return json.loads(raw)
            if raw in ("true", "false"):
                return raw == "true"
            return int(raw)
    return None


def tier_reducer() -> str:
    val = _toml_field("tier_reducer")
    return str(val) if val is not None else "min"


def journal_pin() -> int:
    val = _toml_field("journal_pin")
    return int(val) if val is not None else 0


def seq_floor() -> int:
    val = _toml_field("seq_floor")
    return int(val) if val is not None else 0


def replay_gate() -> int:
    val = _toml_field("replay_gate")
    return int(val) if val is not None else 0


def read_runtime() -> dict:
    return json.loads((DATA / "state" / "runtime.json").read_text())


def tier_head(path: Path) -> int:
    head = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        head = max(head, int(rec["seq"]))
    return head


def resolve_seq(movement_dir: Path | None = None) -> int:
    root = movement_dir or (DATA / "movements")
    mode = tier_reducer()
    pick = None
    for path in sorted(root.glob("tier_*.jsonl")):
        head = tier_head(path)
        if pick is None:
            pick = head
            continue
        if mode == "min" and head < pick:
            pick = head
        if mode != "min" and head > pick:
            pick = head
    if pick is None or pick == 0:
        raise FileNotFoundError("no movement tiers")
    return int(pick)


def seq_cut(runtime: dict, floor: int) -> int:
    s = int(runtime["active_seq"])
    if floor > 0 and floor < s:
        s = floor
    movement_head = int(runtime["movement_head"])
    if s > movement_head:
        s = movement_head
    return s


def load_events(events_dir: Path | None = None) -> list[dict]:
    root = events_dir or (DATA / "events")
    rows = []
    for path in sorted(root.glob("evt_*.json")):
        rows.append(json.loads(path.read_text()))
    rows.sort(key=lambda r: int(r["seq"]))
    return rows


def apply_event(tracks: dict[str, list[str]], row: dict) -> None:
    track = row["track"]
    car = row["car"]
    tracks.setdefault(track, [])
    if row["op"] == "place":
        pos = int(row.get("pos", 0))
        tracks[track] = [c for c in tracks[track] if c != car]
        pos = max(0, min(pos, len(tracks[track])))
        tracks[track].insert(pos, car)
    elif row["op"] == "pull":
        tracks[track] = [c for c in tracks[track] if c != car]


def consist_at(rows: list[dict], seq: int, *, allow_pulls: bool = True) -> dict[str, list[str]]:
    tracks: dict[str, list[str]] = {}
    for row in rows:
        if int(row["seq"]) > seq:
            break
        if row["op"] == "pull" and not allow_pulls:
            continue
        apply_event(tracks, row)
    return {k: tracks[k][:] for k in sorted(tracks)}


def audit_digest(tracks: dict[str, list[str]]) -> str:
    body = json.dumps(tracks, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def build_report() -> dict:
    runtime = read_runtime()
    floor = seq_floor()
    pin = journal_pin()
    seq = seq_cut(runtime, floor)
    rows = load_events()
    if pin > 0:
        rows = [row for row in rows if int(row["seq"]) <= pin]
    tracks = consist_at(rows, seq, allow_pulls=True)
    return {
        "replay_seq": seq,
        "tracks": tracks,
        "audit_digest": audit_digest(tracks),
    }
