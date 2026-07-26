#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="${APP_ROOT:-/app}"
OUT="${OUT:-/output/thermal-conserve-report.json}"
POLICY="$APP_ROOT/data/policy"

mkdir -p "$APP_ROOT/knit_x" "$APP_ROOT/fold_y" "$APP_ROOT/slot_z" "$(dirname "$OUT")" "$POLICY"
cp "$ROOT_DIR/knit_x/op_a.py" "$APP_ROOT/knit_x/op_a.py"
cp "$ROOT_DIR/fold_y/op_b.py" "$APP_ROOT/fold_y/op_b.py"
cp "$ROOT_DIR/slot_z/op_c.py" "$APP_ROOT/slot_z/op_c.py"
touch "$APP_ROOT/knit_x/__init__.py" "$APP_ROOT/fold_y/__init__.py" "$APP_ROOT/slot_z/__init__.py"

# Accept handoff so evaluation prep does not rematerialize the trial preference.
printf 'accepted\n' > "$POLICY/handoff.accept"
rm -f "$POLICY/trial_pref.live"

export APP_ROOT
export OUT
export PYTHONPATH="$APP_ROOT:${PYTHONPATH:-}"

bash "$APP_ROOT/scripts/prep_eval.sh"

python3 <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path

app = Path(os.environ["APP_ROOT"])
out = Path(os.environ["OUT"])
sys.path.insert(0, str(app))

from knit_x.op_a import op_a, scale_for
from fold_y.op_b import fold_batches, op_b
from slot_z.op_c import op_c, preview_dt
from solver.core.step import load_profile, run_pack

# Smoke repaired numerical helpers.
probe_g = scale_for("gap")
probe_w = op_a("weld", None)
assert probe_g < probe_w
folded = op_b([("c0", -1.5), ("c1", 1.5)], "compensated")
assert abs(folded["c0"] + folded["c1"]) < 1e-12
batch = fold_batches([[("c0", -0.25), ("c1", 0.25)]], None)
assert abs(batch["c0"] + batch["c1"]) < 1e-12
dt_info = preview_dt("cfl", {"C_list": [1.0, 1.2], "Gmax": 2.0})
assert dt_info["token"] == "cfl" and 0.0 < dt_info["dt"] < 0.1
fixed = op_c("fixed", {"C_list": [1.0], "Gmax": 1.0})
assert fixed[1] == "fixed"

# Trial preference must not override accepted profile tokens.
ship = load_profile(app / "config/profiles/ship.toml")
assert ship["contact_model"] == "gap_rc"
assert ship["reduction_order"] == "compensated"
assert ship["dt_policy"] == "cfl"

pack = json.loads((app / "data/packs/pack_alpha.json").read_text())
direct = run_pack(pack, ship)
rel = abs(direct["E1"] - direct["E0"]) / max(abs(direct["E0"]), 1e-15)
assert rel <= 1e-9

desk = app / "scripts" / "run_thermal_eval.sh"
subprocess.check_call(["bash", str(desk)])
first = out.read_bytes()
subprocess.check_call(["bash", str(desk)])
second = out.read_bytes()
if first != second:
    raise SystemExit("thermal report is not byte-idempotent")

card = json.loads(first.decode())
if card.get("status") != "ok":
    raise SystemExit(f"report status not ok: {card.get('status')}")
ids = {row["profile_id"] for row in card.get("profiles", [])}
if ids != {"ship", "fleet"}:
    raise SystemExit(f"expected ship+fleet profiles, got {sorted(ids)}")
for row in card["profiles"]:
    if row["energy_rel_err"] > 1e-9:
        raise SystemExit(f"energy band miss on {row['profile_id']}")
    if row["hotspot_rel_err"] > 1e-6:
        raise SystemExit(f"hotspot band miss on {row['profile_id']}")
    if row["max_dT_K"] > 1e-4:
        raise SystemExit(f"dT band miss on {row['profile_id']}")

print(f"oracle desk ok -> {out}", file=sys.stderr)
PY

test -f "$OUT"
test -f "$POLICY/handoff.accept"
test ! -f "$POLICY/trial_pref.live"
