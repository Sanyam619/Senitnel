#!/bin/bash
set -euo pipefail

DISTRO_ROOT="${DISTRO_ROOT:-/opt/distro}"

mkdir -p "$DISTRO_ROOT/mod_a" "$DISTRO_ROOT/mod_b" "$DISTRO_ROOT/mod_c"
touch "$DISTRO_ROOT/mod_a/__init__.py" \
  "$DISTRO_ROOT/mod_b/__init__.py" \
  "$DISTRO_ROOT/mod_c/__init__.py"

cat > "$DISTRO_ROOT/mod_a/op_a.py" <<'EOF'
"""Opaque helper — marginal token recovery."""


def op_a(a, b):
    """Return highest offer among positive assignments in mapping b using row table a."""
    idx = {r[0]: r for r in a}
    offers = []
    for uid, mw in b.items():
        if mw > 0:
            offers.append(idx[uid][2])
    if not offers:
        raise ValueError("empty")
    return max(offers)


def binds_flag(a, b, need):
    idx = {r[0]: r for r in a}
    room = 0
    for uid, mw in b.items():
        if mw > 0:
            room += idx[uid][1] - mw
    return room == need
EOF

cat > "$DISTRO_ROOT/mod_b/op_b.py" <<'EOF'
"""Opaque helper — status classification and cleared rows."""

from __future__ import annotations

from pathlib import Path


def _parse(text: str):
    rid = ""
    demand = 0
    reserve = 0
    rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("round_id:"):
            rid = line.split(":", 1)[1].strip()
        elif line.startswith("demand_mw:"):
            demand = int(line.split(":", 1)[1].strip())
        elif line.startswith("reserve_mw:"):
            reserve = int(line.split(":", 1)[1].strip())
        elif line.startswith("unit "):
            p = line.split()
            rows.append((p[1], int(p[2]), int(p[3])))
    return rid, demand, reserve, rows


def _clears(demand, rows):
    n = len(rows)
    out = []

    def rec(online_idx, cur, sumv):
        if len(cur) == len(online_idx):
            if sumv == demand:
                out.append({rows[i][0]: cur[j] for j, i in enumerate(online_idx)})
            return
        j = len(cur)
        i = online_idx[j]
        cap = rows[i][1]
        rem_max = sum(rows[online_idx[k]][1] for k in range(j + 1, len(online_idx)))
        for mw in range(1, cap + 1):
            if sumv + mw > demand:
                break
            if sumv + mw + rem_max < demand:
                continue
            cur.append(mw)
            rec(online_idx, cur, sumv + mw)
            cur.pop()

    for mask in range(1, 1 << n):
        online = [i for i in range(n) if mask & (1 << i)]
        if sum(rows[i][1] for i in online) < demand:
            continue
        rec(online, [], 0)
    return out


def _room(rows, cleared):
    idx = {r[0]: r for r in rows}
    return sum(idx[u][1] - mw for u, mw in cleared.items() if mw > 0)


def _smp(rows, cleared):
    idx = {r[0]: r for r in rows}
    return max(idx[u][2] for u, mw in cleared.items() if mw > 0)


def op_b(a, b):
    """
    a: path to sheet (str)
    b: unused
    returns dict with rid, status, cleared, reserve, rows
    """
    rid, demand, reserve, rows = _parse(Path(a).read_text())
    energy_example = None
    feasible_example = None
    best_f = None
    best_e = None
    energy_ok = False
    reserve_ok = False
    for cleared in _clears(demand, rows):
        energy_ok = True
        skey = (_smp(rows, cleared), tuple(sorted(cleared.items())))
        if best_e is None or skey < best_e[0]:
            best_e = (skey, cleared)
            energy_example = cleared
        if _room(rows, cleared) >= reserve:
            reserve_ok = True
            fkey = (
                _smp(rows, cleared),
                -_room(rows, cleared),
                tuple(sorted(cleared.items())),
            )
            if best_f is None or fkey < best_f[0]:
                best_f = (fkey, cleared)
                feasible_example = cleared
    if not energy_ok:
        return {
            "rid": rid,
            "status": "infeasible",
            "cleared": {},
            "reserve": reserve,
            "rows": rows,
            "clause": "C_CAP",
        }
    if not reserve_ok:
        return {
            "rid": rid,
            "status": "reserve_short",
            "cleared": dict(energy_example or {}),
            "reserve": reserve,
            "rows": rows,
            "clause": "C_RES",
        }
    return {
        "rid": rid,
        "status": "feasible_clear",
        "cleared": dict(feasible_example or {}),
        "reserve": reserve,
        "rows": rows,
        "clause": None,
    }
EOF

cat > "$DISTRO_ROOT/mod_c/op_c.py" <<'EOF'
"""Opaque helper — refutations and card emission."""

from __future__ import annotations

import json
from pathlib import Path


def op_c(a, b):
    """
    a: list of per-round dicts from op_b enriched with smp/binds
    b: output path
    """
    rounds = []
    for row in a:
        status = row["status"]
        cleared_map = row["cleared"]
        rows = row["rows"]
        idx = {r[0]: r for r in rows}
        cleared = [
            {
                "unit_id": uid,
                "mw": int(mw),
                "offer_price": int(idx[uid][2]),
            }
            for uid, mw in sorted(cleared_map.items())
            if mw > 0
        ]
        item = {
            "round_id": row["rid"],
            "cleared": cleared,
            "smp": int(row.get("smp", 0)),
            "reserve_binds": bool(row.get("binds", False)),
            "status": status,
        }
        if status in ("infeasible", "reserve_short"):
            item["refutation"] = row["clause"]
            if status == "infeasible":
                item["cleared"] = []
                item["smp"] = 0
        rounds.append(item)
    card = {"version": 1, "rounds": rounds}
    path = Path(b)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(card, sort_keys=True, separators=(",", ":")) + "\n")
    return str(path)
EOF


bash "$DISTRO_ROOT/scripts/run-cycle.sh"
test -f /data/out/answers.json
