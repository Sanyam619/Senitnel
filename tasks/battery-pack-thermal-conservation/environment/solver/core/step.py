"""Core pack advance — finite-volume thermal step with policy bind."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(pkg: str, attr: str):
    return getattr(importlib.import_module(pkg), attr)


_conduct = _load("knit_x.op" + "_a", "op" + "_a")
_fold = _load("fold_y.op" + "_b", "op" + "_b")
_dtpick = _load("slot_z.op" + "_c", "op" + "_c")
_skim = _load("solver.decoy.skim_w", "skim")


def _parse_toml_map(path: Path) -> dict:
    out = {}
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"')
    return out


def load_profile(path: Path) -> dict:
    """Bind profile tokens, applying fleet-trial preference when unaccepted."""
    out = _parse_toml_map(path)
    policy_dir = ROOT / "data" / "policy"
    accepted = (policy_dir / "handoff.accept").is_file()
    trial = policy_dir / "trial_pref.live"
    if trial.is_file() and not accepted:
        over = _parse_toml_map(trial)
        for key in ("contact_model", "reduction_order", "dt_policy"):
            if key in over:
                out[key] = over[key]
    return out


def run_pack(pack: dict, profile: dict) -> dict:
    cells = {c["id"]: {"C": float(c["C"]), "T": float(c["T0"])} for c in pack["cells"]}
    order = [c["id"] for c in pack["cells"]]
    e0 = sum(cells[i]["C"] * cells[i]["T"] for i in order)
    contact_model = profile["contact_model"]
    use_mat = contact_model == "gap_rc"

    gmax = 0.0
    for link in pack["links"]:
        mat = link["material"] if use_mat else "weld"
        g = float(link["K"]) * float(_conduct(mat, contact_model))
        gmax = max(gmax, g)

    c_list = [cells[i]["C"] for i in order]
    dt, dt_token = _dtpick(profile["dt_policy"], {"C_list": c_list, "Gmax": gmax})
    red = profile["reduction_order"]

    for _ in range(int(pack["steps"])):
        contrib = []
        for link in pack["links"]:
            mat = link["material"] if use_mat else "weld"
            g = float(link["K"]) * float(_conduct(mat, None))
            a, b = link["a"], link["b"]
            d_t = cells[a]["T"] - cells[b]["T"]
            flux = g * d_t * dt
            contrib.append((a, -flux))
            contrib.append((b, +flux))
        folded = _fold(contrib, red)
        for cid, de in folded.items():
            cells[cid]["T"] += de / cells[cid]["C"]
        _skim([cells[i]["T"] for i in order], None)

    e1 = sum(cells[i]["C"] * cells[i]["T"] for i in order)
    tvec = [cells[i]["T"] for i in order]
    return {
        "T": tvec,
        "ids": order,
        "E0": e0,
        "E1": e1,
        "contact_model": contact_model,
        "reduction_order": red,
        "dt_policy": dt_token,
        "dt": dt,
    }


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--pack", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    pack = json.loads(Path(args.pack).read_text())
    profile = load_profile(Path(args.profile))
    result = run_pack(pack, profile)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
