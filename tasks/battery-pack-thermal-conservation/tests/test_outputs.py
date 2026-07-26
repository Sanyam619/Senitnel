"""Verifier for pack thermal conservation — domain residuals, not schema-only."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/thermal-conserve-report.json")
APP = Path("/app")
BANDS = {"max_energy_rel_err": 1e-9, "max_hotspot_rel_err": 1e-6, "max_dT_K": 1e-4}
POLICY = APP / "data/policy"


def _load():
    assert REPORT.exists(), "missing graded report"
    return json.loads(REPORT.read_text())


def _profiles(card):
    return {p["profile_id"]: p for p in card["profiles"]}


def _prof_toml(pid: str) -> dict:
    out = {}
    for line in (APP / f"config/profiles/{pid}.toml").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def _run_pack(pid: str, pack_name: str):
    import sys

    sys.path.insert(0, str(APP))
    from solver.core.step import load_profile, run_pack

    pack = json.loads((APP / "data/packs" / pack_name).read_text())
    profile = load_profile(APP / "config/profiles" / f"{pid}.toml")
    return run_pack(pack, profile), pack


def _seed_tokens() -> dict:
    out = {}
    for line in (POLICY / "trial_pref.seed").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def test_k3_zircon():
    """Both profiles present with status ok and residual fields under band."""
    card = _load()
    assert card["status"] == "ok"
    assert isinstance(card["eval_sha"], str) and len(card["eval_sha"]) >= 32
    assert card["run_stamp"] == "thermal-v1"
    ids = {p["profile_id"] for p in card["profiles"]}
    assert ids == {"ship", "fleet"}
    for p in card["profiles"]:
        for key in (
            "energy_rel_err",
            "hotspot_rel_err",
            "max_dT_K",
            "contact_model",
            "reduction_order",
            "dt_policy",
        ):
            assert key in p
        # Schema alone is not enough: residuals must already sit in band.
        assert p["energy_rel_err"] <= BANDS["max_energy_rel_err"]
        assert p["hotspot_rel_err"] <= BANDS["max_hotspot_rel_err"]


def test_v4_jade():
    """Ship energy residual within band and matches independent recompute."""
    p = _profiles(_load())["ship"]
    assert p["energy_rel_err"] <= BANDS["max_energy_rel_err"]
    direct, _ = _run_pack("ship", "pack_alpha.json")
    rel = abs(direct["E1"] - direct["E0"]) / max(abs(direct["E0"]), 1e-15)
    assert rel <= BANDS["max_energy_rel_err"]
    assert rel <= p["energy_rel_err"] + 1e-15


def test_p2_garnet():
    """Hotspot residuals and max dT within bands for both profiles."""
    for pid, p in _profiles(_load()).items():
        assert p["hotspot_rel_err"] <= BANDS["max_hotspot_rel_err"], pid
        assert p["max_dT_K"] <= BANDS["max_dT_K"], pid


def test_r1_onyx():
    """Policy tokens match declared profiles and survive sealed evaluation prep."""
    for pid, p in _profiles(_load()).items():
        want = _prof_toml(pid)
        assert p["contact_model"] == want["contact_model"] == "gap_rc"
        assert p["reduction_order"] == want["reduction_order"] == "compensated"
        assert p["dt_policy"] == want["dt_policy"]
    subprocess.run(["bash", str(APP / "scripts/prep_eval.sh")], check=True)
    subprocess.run(["bash", str(APP / "scripts/run_thermal_eval.sh")], check=True)
    for pid, p in _profiles(_load()).items():
        want = _prof_toml(pid)
        assert p["contact_model"] == want["contact_model"]
        assert p["reduction_order"] == want["reduction_order"]
        assert p["dt_policy"] == want["dt_policy"]
        seed = _seed_tokens()
        assert p["contact_model"] != seed["contact_model"]


def test_w9_flint():
    """Report entrypoint is byte-idempotent with bands still green."""
    before = REPORT.read_bytes()
    subprocess.run(["bash", str(APP / "scripts/run_thermal_eval.sh")], check=True)
    after = REPORT.read_bytes()
    assert before == after
    card = _load()
    assert card["status"] == "ok"
    for p in card["profiles"]:
        assert p["energy_rel_err"] <= BANDS["max_energy_rel_err"]


def test_q7_topaz():
    """Fleet energy residual within band under fixed dt_policy."""
    p = _profiles(_load())["fleet"]
    assert p["energy_rel_err"] <= BANDS["max_energy_rel_err"]
    assert p["dt_policy"] == "fixed"
    direct, _ = _run_pack("fleet", "pack_beta.json")
    rel = abs(direct["E1"] - direct["E0"]) / max(abs(direct["E0"]), 1e-15)
    assert rel <= BANDS["max_energy_rel_err"]


def test_t6_amber():
    """Surface dashboard greens while deep residuals remain the authority."""
    assert (APP / "bin/thermalsurf").exists()
    proc = subprocess.run(
        ["bash", str(APP / "bin/thermalsurf")],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "status=ok" in proc.stdout
    card = _load()
    assert card["status"] == "ok"
    for p in card["profiles"]:
        assert p["energy_rel_err"] <= BANDS["max_energy_rel_err"]
        assert p["hotspot_rel_err"] <= BANDS["max_hotspot_rel_err"]
    # Surface ok is not enough if ship and fleet advances collapsed together.
    s_direct, _ = _run_pack("ship", "pack_gamma.json")
    f_direct, _ = _run_pack("fleet", "pack_gamma.json")
    assert s_direct["T"] != f_direct["T"]


def test_m8_obsidian():
    """Accepted handoff leaves receipt, no trial pref, report still ok."""
    assert (POLICY / "handoff.accept").is_file()
    subprocess.run(["bash", str(APP / "scripts/prep_eval.sh")], check=True)
    assert (POLICY / "handoff.accept").is_file()
    assert not (POLICY / "trial_pref.live").exists()
    subprocess.run(["bash", str(APP / "scripts/run_thermal_eval.sh")], check=True)
    card = _load()
    assert card["status"] == "ok"
    ledger = (APP / "data/packs/LEDGER.sha256").read_text().strip()
    assert card["eval_sha"] == ledger
    # Tokens must still be profile-declared after sealed evaluation prep.
    for pid, p in _profiles(card).items():
        want = _prof_toml(pid)
        assert p["contact_model"] == want["contact_model"]
        assert p["reduction_order"] == want["reduction_order"]


def test_n5_beryl():
    """Canceling-flux pack conserves energy under ship (direct solver path)."""
    direct, pack = _run_pack("ship", "pack_alpha.json")
    assert pack["pack_id"] == "alpha"
    rel = abs(direct["E1"] - direct["E0"]) / max(abs(direct["E0"]), 1e-15)
    assert rel <= BANDS["max_energy_rel_err"]
    assert direct["contact_model"] == "gap_rc"
    assert direct["reduction_order"] == "compensated"


def test_y3_coral():
    """Ship hotspot matches frozen refs on every pack (independent of report)."""
    ref = json.loads((APP / "data/refs/ship_ref.json").read_text())
    for pack_path in sorted((APP / "data/packs").glob("pack_*.json")):
        direct, pack = _run_pack("ship", pack_path.name)
        Tr = ref["packs"][pack["pack_id"]]["T"]
        T = direct["T"]
        assert len(T) == len(Tr)
        denom = max(max(abs(x) for x in Tr), 1e-15)
        hotspot = max(abs(a - b) for a, b in zip(T, Tr)) / denom
        max_dt = max(abs(a - b) for a, b in zip(T, Tr))
        assert hotspot <= BANDS["max_hotspot_rel_err"], pack["pack_id"]
        assert max_dt <= BANDS["max_dT_K"], pack["pack_id"]


def test_h2_quartz():
    """Ship CFL vs fleet fixed polarity; both conserve energy."""
    ship = _profiles(_load())["ship"]
    fleet = _profiles(_load())["fleet"]
    assert ship["dt_policy"] == "cfl"
    assert fleet["dt_policy"] == "fixed"
    assert ship["dt_policy"] != fleet["dt_policy"]
    assert ship["energy_rel_err"] <= BANDS["max_energy_rel_err"]
    assert fleet["energy_rel_err"] <= BANDS["max_energy_rel_err"]
    s_direct, _ = _run_pack("ship", "pack_gamma.json")
    f_direct, _ = _run_pack("fleet", "pack_gamma.json")
    assert s_direct["dt_policy"] == "cfl"
    assert f_direct["dt_policy"] == "fixed"
    assert s_direct["T"] != f_direct["T"]


def test_s4_opal():
    """Trial preference is not graded authority; accept leaves handoff.accept and no live file."""
    seed = _seed_tokens()
    assert seed["contact_model"] == "weld_face"
    assert seed["reduction_order"] == "truncate"
    card = _load()
    for p in card["profiles"]:
        assert p["contact_model"] != seed["contact_model"]
        assert p["reduction_order"] != seed["reduction_order"]
        want = _prof_toml(p["profile_id"])
        assert p["contact_model"] == want["contact_model"]
        assert p["reduction_order"] == want["reduction_order"]
    assert (POLICY / "handoff.accept").is_file()
    assert not (POLICY / "trial_pref.live").exists()
