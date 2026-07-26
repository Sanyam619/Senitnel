#!/bin/bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
OUT="${OUT:-/output/thermal-conserve-report.json}"
mkdir -p "$(dirname "$OUT")" /tmp/thermal_runs

python3 - "$APP_ROOT" "$OUT" <<'PY'
import hashlib, json, sys
from pathlib import Path

app = Path(sys.argv[1])
out = Path(sys.argv[2])
sys.path.insert(0, str(app))
from solver.core.step import load_profile, run_pack, _parse_toml_map

ledger = (app / "data/packs/LEDGER.sha256").read_text().strip()
h = hashlib.sha256()
for p in sorted((app / "data/packs").glob("pack_*.json")):
    h.update(p.read_bytes())
eval_sha = h.hexdigest()
if eval_sha != ledger:
    raise SystemExit("fixture ledger mismatch")

bands = {"max_energy_rel_err": 1e-9, "max_hotspot_rel_err": 1e-6, "max_dT_K": 1e-4}
profiles_out = []
for prof_path in sorted((app / "config/profiles").glob("*.toml")):
    profile = load_profile(prof_path)
    declared = _parse_toml_map(prof_path)
    pid = declared["profile_id"]
    ref = json.loads((app / "data/refs" / f"{pid}_ref.json").read_text())
    energy_errs = []
    hotspot_errs = []
    max_dts = []
    tokens = None
    for pack_path in sorted((app / "data/packs").glob("pack_*.json")):
        pack = json.loads(pack_path.read_text())
        r = run_pack(pack, profile)
        tokens = (r["contact_model"], r["reduction_order"], r["dt_policy"])
        E0, E1 = r["E0"], r["E1"]
        energy_errs.append(abs(E1 - E0) / max(abs(E0), 1e-15))
        Tr = ref["packs"][pack["pack_id"]]["T"]
        T = r["T"]
        denom = max(max(abs(x) for x in Tr), 1e-15)
        hotspot_errs.append(max(abs(a - b) for a, b in zip(T, Tr)) / denom)
        max_dts.append(max(abs(a - b) for a, b in zip(T, Tr)))
    row = {
        "profile_id": pid,
        "energy_rel_err": max(energy_errs),
        "hotspot_rel_err": max(hotspot_errs),
        "max_dT_K": max(max_dts),
        "contact_model": tokens[0],
        "reduction_order": tokens[1],
        "dt_policy": tokens[2],
    }
    profiles_out.append(row)

report = {
    "status": "ok",
    "eval_sha": eval_sha,
    "profiles": profiles_out,
    "run_stamp": "thermal-v1",
}
ok = True
for row in profiles_out:
    declared = _parse_toml_map(app / "config/profiles" / f"{row['profile_id']}.toml")
    if row["energy_rel_err"] > bands["max_energy_rel_err"]:
        ok = False
    if row["hotspot_rel_err"] > bands["max_hotspot_rel_err"]:
        ok = False
    if row["max_dT_K"] > bands["max_dT_K"]:
        ok = False
    if row["contact_model"] != declared["contact_model"]:
        ok = False
    if row["reduction_order"] != declared["reduction_order"]:
        ok = False
    if row["dt_policy"] != declared["dt_policy"]:
        ok = False
report["status"] = "ok" if ok else "fail"
out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
print(report["status"], out)
PY
