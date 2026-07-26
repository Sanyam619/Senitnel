#!/usr/bin/env python3
"""Stage K7: ingest drill exports into a work bundle."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def pull(root: Path) -> dict:
    scenarios = {}
    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        meta = {}
        for line in _lines(child / "meta.properties"):
            if "=" in line:
                k, v = line.split("=", 1)
                meta[k.strip()] = v.strip()
        members = [m.strip() for m in meta.get("members", "").split(",") if m.strip()]
        rows = {}
        for line in _lines(child / "coordinator.log"):
            parts = line.split()
            if len(parts) >= 4 and parts[0] == "TX" and parts[2] == "DECISION":
                rows[parts[1]] = parts[3]
        units = []
        for member in members:
            for line in _lines(child / f"member-{member}.log"):
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "TX":
                    if parts[2] == "ABORTED":
                        continue
                    units.append({"src": member, "id": parts[1], "state": parts[2]})
        actions = []
        group = ""
        txid = ""
        for line in _lines(child / "saga.plan"):
            parts = line.split()
            if len(parts) >= 4 and parts[0] == "SAGA":
                group = parts[1]
                txid = parts[3]
            elif len(parts) >= 4 and parts[0] == "STEP":
                actions.append(
                    {"group": group, "id": txid, "state": parts[2], "label": parts[3]}
                )
        scenarios[child.name] = {
            "mode": meta.get("mode", "PA"),
            "members": members,
            "rows": rows,
            "units": units,
            "actions": actions,
        }
    return {"scenarios": scenarios}


def _lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def main() -> int:
    root = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    dest.write_text(json.dumps(pull(root)) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
