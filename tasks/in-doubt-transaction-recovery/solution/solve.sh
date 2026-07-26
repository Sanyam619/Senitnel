#!/bin/bash
set -euo pipefail

mkdir -p /app/k7 /app/m3 /app/r9 /app/w2

cat > /app/k7/k7.py <<'PY'
#!/usr/bin/env python3
"""Stage K7: ingest drill exports into a work bundle."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def _meta(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _lines(path):
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _rows(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _lines(path):
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "TX" and parts[2] == "DECISION":
            values[parts[1]] = parts[3]
    return values


def _units(dir_path: Path, members: list[str]) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for member in members:
        for line in _lines(dir_path / f"member-{member}.log"):
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "TX":
                values.append({"src": member, "id": parts[1], "state": parts[2]})
    return values


def _actions(path: Path) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    group = ""
    txid = ""
    for line in _lines(path):
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "SAGA":
            group = parts[1]
            txid = parts[3]
        elif len(parts) >= 4 and parts[0] == "STEP":
            values.append(
                {"group": group, "id": txid, "state": parts[2], "label": parts[3]}
            )
    return values


def pull(root: Path) -> dict:
    scenarios: dict[str, dict] = {}
    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        meta = _meta(child / "meta.properties")
        members = [m.strip() for m in meta.get("members", "").split(",") if m.strip()]
        scenarios[child.name] = {
            "mode": meta.get("mode", "PA"),
            "members": members,
            "rows": _rows(child / "coordinator.log"),
            "units": _units(child, members),
            "actions": _actions(child / "saga.plan"),
        }
    return {"scenarios": scenarios}


def main() -> int:
    root = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    dest.write_text(json.dumps(pull(root), sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

cat > /app/m3/m3.py <<'PY'
#!/usr/bin/env python3
"""Stage M3: flatten member rows per transfer."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def gather(payload: dict) -> dict:
    out = {"scenarios": {}}
    for name, bundle in payload["scenarios"].items():
        staged: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        for unit in bundle["units"]:
            staged[unit["id"]][unit["src"]].append(unit["state"])
        grouped: dict[str, list[str]] = {}
        for txid, members in staged.items():
            flat: list[str] = []
            for member in sorted(members):
                seen: dict[str, bool] = {}
                for state in members[member]:
                    seen[state] = True
                for state in seen:
                    flat.append(f"{member}:{state}")
            grouped[txid] = flat
        out["scenarios"][name] = {
            "mode": bundle["mode"],
            "members": list(bundle["members"]),
            "rows": dict(bundle["rows"]),
            "actions": list(bundle["actions"]),
            "grouped": grouped,
        }
    return out


def main() -> int:
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    payload = json.loads(src.read_text(encoding="utf-8"))
    dest.write_text(json.dumps(gather(payload), sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

cat > /app/r9/r9.py <<'PY'
#!/usr/bin/env python3
"""Stage R9: emit transfer decisions."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def pick(coord, fragments, mode, member_count):
    done = False
    stopped = False
    prepared: set[str] = set()
    for raw in fragments:
        member = ""
        state = raw
        if ":" in raw:
            member, state = raw.split(":", 1)
        if state == "COMMITTED":
            done = True
        elif state == "ABORTED":
            stopped = True
        elif state == "PREPARED":
            prepared.add(member or raw)
    if stopped:
        return "ABORT"
    if done:
        return "COMMIT"
    if coord is not None:
        return coord
    if mode == "PC" and len(prepared) >= member_count:
        return "COMMIT"
    return "ABORT"


def weave(payload: dict) -> dict:
    out = {"scenarios": {}}
    for name, bundle in payload["scenarios"].items():
        ids = set(bundle["rows"]) | set(bundle["grouped"])
        for action in bundle["actions"]:
            if action.get("id"):
                ids.add(action["id"])
        decisions = {}
        for txid in sorted(ids):
            decisions[txid] = pick(
                bundle["rows"].get(txid),
                bundle["grouped"].get(txid, []),
                bundle["mode"],
                len(bundle["members"]),
            )
        out["scenarios"][name] = {
            "actions": list(bundle["actions"]),
            "decisions": decisions,
        }
    return out


def main() -> int:
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    payload = json.loads(src.read_text(encoding="utf-8"))
    dest.write_text(json.dumps(weave(payload), sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

cat > /app/w2/w2.py <<'PY'
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
        by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
        for action in bundle["actions"]:
            by_group[action["group"]].append(action)
        sagas: dict[str, list[str]] = {}
        for group, steps in by_group.items():
            ordered = list(reversed(steps))
            txid = ordered[0]["id"] if ordered else ""
            if bundle["decisions"].get(txid) == "COMMIT":
                sagas[group] = []
                continue
            labels: list[str] = []
            for action in ordered:
                if action["state"] == "APPLIED":
                    labels.append(action["label"])
            sagas[group] = labels
        out["scenarios"][name] = {
            "decisions": dict(bundle["decisions"]),
            "sagas": sagas,
        }
    return out


def main() -> int:
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    payload = json.loads(src.read_text(encoding="utf-8"))
    dest.write_text(json.dumps(arrange(payload), sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x /app/k7/*.py /app/m3/*.py /app/r9/*.py /app/w2/*.py /app/ops/tools/replay.sh
