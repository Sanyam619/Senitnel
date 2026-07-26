"""Verifier for ceremony UV/UP live-state seating recovery."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

OUTPUT = Path("/output/ceremony-ledger.json")
QUARANTINE = Path("/output/quarantine.json")
FIXTURES = Path("/app/data/fixtures")
SURFACE = FIXTURES / "surface_attestation.json"
SEED = FIXTURES / "seed.json"
SEGMENTS = Path("/app/data/signed_segments")
TRUSTEVAL = Path("/usr/lib/ceremony/bin/trusteval")
APP_TRUSTEVAL = Path("/app/bin/trusteval")
RUN_MESH = "/app/ops/run_mesh.sh"
DYNAMIC_FRAME = FIXTURES / "dynamic_test_frame.bin"
DYNAMIC_INJECTED = FIXTURES / "dynamic_test_injected.bin"
DYNAMIC_LEGACY = FIXTURES / "dynamic_test_legacy.bin"

EPOCH_10_ACCEPTED = 8
EPOCH_20_ACCEPTED = 5
EPOCH_30_ACCEPTED = 3
EPOCH_40_ACCEPTED = 5
EPOCH_50_ACCEPTED = 4
SURFACE_EPOCH_10 = 10
SCHEMA_VERSION = 1
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
PROFILE_A = "fleet_a"
PROFILE_B = "fleet_b"
BACKEND_NAMES = {"mqtt", "lora", "uart", "canbus", "zigbee"}
PUBLISHED_EPOCHS = {10, 20, 30, 40, 50}
CORE_EPOCHS = {10, 20, 40, 50}
REASON_INTEGRITY = "integrity_failure"
REASON_REPLAY = "replay"
REASON_REVOKED = "revoked"
QUARANTINE_REASONS = (REASON_INTEGRITY, REASON_REPLAY, REASON_REVOKED)
KEY_BACKENDS = "backends"
KEY_EPOCHS = "epochs"
KEY_REJECTED = "rejected"
KEY_EPOCH = "epoch"
KEY_LANE = "lane"
KEY_TS = "ts"
EPOCH_TEN = 10
EPOCH_THIRTY = 30
EPOCH_TWENTY_FIVE = 25
BAND_LO = 2
BAND_HI = 4
BAND_CAP = 6
BACKEND_COUNT = 5
SAMPLE_A = "sample_a"
SAMPLE_B = "sample_b"
SAMPLE_C = "sample_c"
SEED_NAME = "lane-lattice-v2"
DOMAIN_ASCII = "domain_ascii=WAUV"

UV_POLICY = Path("/var/lib/ceremony/state/uv_policy.conf")
HOLD_BOUND = Path("/var/lib/ceremony/state/hold_bound")
STREAM_ORDER = Path("/var/lib/ceremony/state/stream.order")
CUTOVER_OK = Path("/var/lib/ceremony/state/cutover.ok")
GEN_TARGET = Path("/var/lib/ceremony/state/gen.target")
LIVE_LOCAL = Path("/etc/ceremony/reconcile.d/90-local.conf")
ABORT_LOCAL = Path("/var/lib/ceremony/ops/abort.d/90-local.conf")
SITE_STANDARD = Path("/etc/ceremony/site_standard.conf")
RECONCILE = Path("/etc/ceremony/reconcile.conf")

# Verifier-owned EXPECTED (not derived from agent-editable binaries).
EXPECTED_EPOCHS = {
    10: (PROFILE_A, EPOCH_10_ACCEPTED),
    20: (PROFILE_A, EPOCH_20_ACCEPTED),
    30: (PROFILE_A, EPOCH_30_ACCEPTED),
    40: (PROFILE_B, EPOCH_40_ACCEPTED),
    50: (PROFILE_B, EPOCH_50_ACCEPTED),
}
EXPECTED_BACKENDS = {
    "mqtt": STATUS_ACTIVE,
    "lora": STATUS_ACTIVE,
    "uart": STATUS_ACTIVE,
    "canbus": STATUS_INACTIVE,
    "zigbee": STATUS_INACTIVE,
}
EXPECTED_INTEGRITY = {
    (10, "lora", 850),
    (10, "mqtt", 920),
    (20, "lora", 1700),
    (20, "mqtt", 1900),
    (30, "lora", 770),
    (30, "lora", 780),
    (40, "uart", 1350),
    (50, "uart", 1050),
    (50, "uart", 1150),
}
EXPECTED_REPLAY = {
    (10, "mqtt", 950),
    (20, "lora", 1200),
    (20, "lora", 1600),
    (40, "uart", 1200),
    (50, "uart", 800),
}
EXPECTED_REVOKED = {
    (20, "lora", 1600),
    (25, "lora", 950),
}


def _attest(out: Path) -> dict:
    assert TRUSTEVAL.is_file(), f"missing verifier-owned {TRUSTEVAL}"
    # Restore agent-visible binary from the sealed copy before behavioral probes.
    if APP_TRUSTEVAL.parent.is_dir():
        shutil.copy2(TRUSTEVAL, APP_TRUSTEVAL)
        APP_TRUSTEVAL.chmod(0o755)
    result = subprocess.run(
        [str(TRUSTEVAL), "attest", "--out", str(out)],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"trusteval attest failed:\n{result.stderr}"
    return _load_roster(out)


def _run_mesh(out: Path) -> dict:
    assert Path(RUN_MESH).is_file(), f"missing {RUN_MESH}"
    if APP_TRUSTEVAL.parent.is_dir():
        shutil.copy2(TRUSTEVAL, APP_TRUSTEVAL)
        APP_TRUSTEVAL.chmod(0o755)
    result = subprocess.run(
        ["bash", RUN_MESH, str(out)],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"run_mesh failed:\n{result.stderr}\n{result.stdout}"
    return _load_roster(out)


def _load_roster(path: Path) -> dict:
    assert path.is_file(), f"missing roster at {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("version") == SCHEMA_VERSION
    return data


def _load_quarantine(path: Path) -> dict:
    assert path.is_file(), f"missing quarantine at {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("version") == SCHEMA_VERSION
    assert KEY_REJECTED in data
    return data


def _reason_keys(data: dict, reason: str) -> set[tuple]:
    return {
        (int(e["epoch"]), e["lane"], int(e["ts"]))
        for e in data["rejected"]
        if e["reason"] == reason
    }


def _kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _status_map(roster: dict) -> dict[str, str]:
    return {row["name"]: row["status"] for row in roster["backends"]}


def _epoch_map(roster: dict) -> dict[int, dict]:
    return {int(row["id"]): row for row in roster["epochs"]}


def _assert_expected_roster(roster: dict) -> None:
    assert roster["version"] == SCHEMA_VERSION
    assert _status_map(roster) == EXPECTED_BACKENDS
    epochs = _epoch_map(roster)
    assert set(epochs.keys()) == PUBLISHED_EPOCHS
    for eid, (profile, accepted) in EXPECTED_EPOCHS.items():
        assert epochs[eid]["profile"] == profile
        assert int(epochs[eid]["accepted"]) == accepted


@pytest.fixture(scope="module")
def agent_roster() -> dict:
    """Agent-published ceremony ledger."""
    return _load_roster(OUTPUT)


@pytest.fixture(scope="module")
def agent_quarantine() -> dict:
    """Agent-published quarantine."""
    return _load_quarantine(QUARANTINE)


def test_roster_structure(agent_roster: dict):
    """Attestation shape plus deep-path signal (not surface-inflated epoch 10)."""
    assert agent_roster["version"] == SCHEMA_VERSION
    assert KEY_BACKENDS in agent_roster
    assert KEY_EPOCHS in agent_roster
    backends = agent_roster["backends"]
    assert len(backends) == BACKEND_COUNT
    names = {b["name"] for b in backends}
    assert names == BACKEND_NAMES
    for b in backends:
        assert b["status"] in (STATUS_ACTIVE, STATUS_INACTIVE)
    epochs = _epoch_map(agent_roster)
    assert CORE_EPOCHS.issubset(epochs.keys())
    assert int(epochs[EPOCH_TEN]["accepted"]) < SURFACE_EPOCH_10
    assert int(epochs[EPOCH_TEN]["accepted"]) >= EPOCH_30_ACCEPTED


def test_c1_flint_uv_up_seating(agent_roster: dict):
    """UV/UP live policy seats fleet_a require both bits; fleet_b requires UP only."""
    pol = _kv(UV_POLICY)
    assert pol.get("fleet_a_uv") == "1"
    assert pol.get("fleet_a_up") == "1"
    assert pol.get("fleet_b_uv") == "0"
    assert pol.get("fleet_b_up") == "1"
    epochs = _epoch_map(agent_roster)
    assert int(epochs[EPOCH_TEN]["accepted"]) == EPOCH_10_ACCEPTED
    assert int(epochs[40]["accepted"]) == EPOCH_40_ACCEPTED


def test_w7_quartz_hold_exclusive(agent_roster: dict):
    """Exclusive hold-bound seating keeps on-boundary credentials usable."""
    assert HOLD_BOUND.read_text(encoding="utf-8").strip() == "exclusive"
    epochs = _epoch_map(agent_roster)
    assert int(epochs[EPOCH_THIRTY]["accepted"]) == EPOCH_30_ACCEPTED


def test_n5_beryl_held_copresence(agent_roster: dict):
    """Held co-presence keeps epoch 30 published with reduced accepted."""
    epochs = _epoch_map(agent_roster)
    assert EPOCH_THIRTY in epochs
    assert epochs[EPOCH_THIRTY]["profile"] == PROFILE_A
    accepted = int(epochs[EPOCH_THIRTY]["accepted"])
    assert BAND_LO <= accepted <= BAND_HI
    assert accepted == EPOCH_30_ACCEPTED
    assert accepted < BAND_CAP


def test_y3_coral_revoked_omits(agent_roster: dict):
    """Required-lane-only-revoked omits epoch 25 from the published set."""
    epochs = _epoch_map(agent_roster)
    assert EPOCH_TWENTY_FIVE not in epochs
    assert set(epochs.keys()) == PUBLISHED_EPOCHS


def test_r3_topaz_replay_interleave(agent_roster: dict):
    """Interleave-asc stream seating fences equal-ts WAL-first replay."""
    assert STREAM_ORDER.read_text(encoding="utf-8").strip() == "interleave-asc"
    epochs = _epoch_map(agent_roster)
    assert int(epochs[10]["accepted"]) == EPOCH_10_ACCEPTED
    assert int(epochs[20]["accepted"]) == EPOCH_20_ACCEPTED
    assert int(epochs[50]["accepted"]) == EPOCH_50_ACCEPTED


def test_j3_pyrite_jarcheck_false_green(agent_roster: dict):
    """Deep ledger disagrees with surface jarcheck fixture on shared epochs."""
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert agent_roster != surface
    assert Path("/app/bin/jarcheck").is_file()
    surface_epochs = {int(e["id"]): e for e in surface["epochs"]}
    roster_epochs = _epoch_map(agent_roster)
    for eid in sorted(PUBLISHED_EPOCHS):
        assert int(roster_epochs[eid]["accepted"]) < int(surface_epochs[eid]["accepted"])


def test_k9_onyx_cutover_suppresses_abort():
    """Matching cutover receipt keeps live 90-local site-standard; abort stays forensic."""
    assert CUTOVER_OK.is_file(), "missing durable cutover receipt"
    receipt = _kv(CUTOVER_OK)
    target = GEN_TARGET.read_text(encoding="utf-8").strip()
    assert receipt.get("mode") == "seal"
    assert receipt.get("gen") == target
    assert LIVE_LOCAL.is_file(), "live 90-local must remain present"
    live = _kv(LIVE_LOCAL)
    site = _kv(SITE_STANDARD)
    assert live.get("authority") == site.get("authority") == "strict-tier"
    abort = _kv(ABORT_LOCAL)
    assert abort.get("authority") == "surface"
    folded = _kv(RECONCILE)
    assert folded.get("authority") == "strict-tier"


def test_authority_correct_tier(agent_roster: dict):
    """Epoch 10 accepted count matches restored deep attestation."""
    epochs = _epoch_map(agent_roster)
    assert int(epochs[EPOCH_TEN]["accepted"]) == EPOCH_10_ACCEPTED


def test_keyed_integrity_rejects_injected(agent_roster: dict):
    """Forged frames must not inflate epoch 10 accepted."""
    epochs = _epoch_map(agent_roster)
    assert int(epochs[EPOCH_TEN]["accepted"]) == EPOCH_10_ACCEPTED
    assert int(epochs[EPOCH_TEN]["accepted"]) < SURFACE_EPOCH_10


def test_copresence_backends(agent_roster: dict):
    """Matrix lanes active; off-matrix inactive; deep path not surface-inflated."""
    statuses = _status_map(agent_roster)
    assert statuses == EXPECTED_BACKENDS


def test_all_epochs_present(agent_roster: dict):
    """All five fleet epochs publish with correct profiles."""
    _assert_expected_roster(agent_roster)


def test_output_matches_expected(agent_roster: dict):
    """On-disk agent output matches verifier-owned EXPECTED tallies."""
    _assert_expected_roster(agent_roster)


def test_m2_jade_attestation_stable(agent_roster: dict):
    """Second mesh publish must match the agent ledger and stay below surface."""
    second = _run_mesh(Path("/tmp") / "out-second.json")
    assert second == agent_roster
    epochs = _epoch_map(second)
    assert int(epochs[EPOCH_TEN]["accepted"]) < SURFACE_EPOCH_10
    assert EPOCH_THIRTY in epochs


def test_ops_reentry_run_mesh(agent_roster: dict):
    """Ops entrypoint re-entry keeps deep tallies after helper seating."""
    reentry = _run_mesh(Path("/tmp") / "out-reentry.json")
    assert reentry == agent_roster
    assert HOLD_BOUND.read_text(encoding="utf-8").strip() == "exclusive"
    assert STREAM_ORDER.read_text(encoding="utf-8").strip() == "interleave-asc"


def test_v4_amber_dynamic_frame_injection():
    """Inject a valid frame via binary (not cargo) and verify incorporation."""
    seg_path = SEGMENTS / "seg_99.bin"
    assert DYNAMIC_FRAME.is_file(), "dynamic test frame fixture missing"
    shutil.copy(DYNAMIC_FRAME, seg_path)
    try:
        roster = _attest(Path("/tmp") / "out-dynamic.json")
        epochs = _epoch_map(roster)
        assert int(epochs[10]["accepted"]) == EPOCH_10_ACCEPTED + 1
    finally:
        seg_path.unlink(missing_ok=True)


def test_dynamic_injected_frame_rejected():
    """Inject a forged frame and verify it is rejected."""
    seg_path = SEGMENTS / "seg_98.bin"
    assert DYNAMIC_INJECTED.is_file(), "dynamic injected frame fixture missing"
    shutil.copy(DYNAMIC_INJECTED, seg_path)
    try:
        roster = _attest(Path("/tmp") / "out-forged.json")
        epochs = _epoch_map(roster)
        assert int(epochs[40]["accepted"]) == EPOCH_40_ACCEPTED
    finally:
        seg_path.unlink(missing_ok=True)


def test_dynamic_legacy_binding_rejected():
    """Payload-only legacy signatures must not raise accepted tallies."""
    seg_path = SEGMENTS / "seg_97.bin"
    assert DYNAMIC_LEGACY.is_file(), "dynamic legacy frame fixture missing"
    shutil.copy(DYNAMIC_LEGACY, seg_path)
    try:
        roster = _attest(Path("/tmp") / "out-legacy.json")
        epochs = _epoch_map(roster)
        assert int(epochs[40]["accepted"]) == EPOCH_40_ACCEPTED
    finally:
        seg_path.unlink(missing_ok=True)


def test_watermark_boundary_included(agent_roster: dict):
    """On-watermark credential at epoch 10 contributes to accepted."""
    epochs = _epoch_map(agent_roster)
    assert int(epochs[EPOCH_TEN]["accepted"]) == EPOCH_10_ACCEPTED


def test_quarantine_structure(agent_quarantine: dict):
    """Quarantine shape and reason vocabulary match expected deep outcomes."""
    assert len(agent_quarantine["rejected"]) == (
        len(EXPECTED_INTEGRITY) + len(EXPECTED_REPLAY) + len(EXPECTED_REVOKED)
    )
    reasons = {e["reason"] for e in agent_quarantine["rejected"]}
    assert REASON_INTEGRITY in reasons
    assert REASON_REPLAY in reasons
    assert REASON_REVOKED in reasons
    for entry in agent_quarantine["rejected"]:
        assert KEY_EPOCH in entry
        assert KEY_LANE in entry
        assert KEY_TS in entry
        assert entry["reason"] in QUARANTINE_REASONS


def test_quarantine_integrity_failures(agent_quarantine: dict):
    """integrity_failure rows match verifier-owned EXPECTED set."""
    assert _reason_keys(agent_quarantine, REASON_INTEGRITY) == EXPECTED_INTEGRITY


def test_quarantine_replay_entries(agent_quarantine: dict):
    """replay rows match verifier-owned EXPECTED set."""
    assert _reason_keys(agent_quarantine, REASON_REPLAY) == EXPECTED_REPLAY


def test_quarantine_revoked_entries(agent_quarantine: dict):
    """revoked rows match verifier-owned EXPECTED set."""
    assert _reason_keys(agent_quarantine, REASON_REVOKED) == EXPECTED_REVOKED


def test_quarantine_matches_expected(agent_quarantine: dict):
    """On-disk quarantine equals the union of EXPECTED reason sets."""
    assert _reason_keys(agent_quarantine, REASON_INTEGRITY) == EXPECTED_INTEGRITY
    assert _reason_keys(agent_quarantine, REASON_REPLAY) == EXPECTED_REPLAY
    assert _reason_keys(agent_quarantine, REASON_REVOKED) == EXPECTED_REVOKED


def test_fixtures_untouched():
    """Seed and surface fixtures remain as shipped."""
    data = json.loads(SEED.read_text(encoding="utf-8"))
    assert data.get("seed") == SEED_NAME
    assert data.get("preserve") is True
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert surface.get("version") == SCHEMA_VERSION
    assert int(surface["epochs"][0]["accepted"]) == SURFACE_EPOCH_10
    audit = (FIXTURES / "pre_incident_audit.log").read_text(encoding="utf-8")
    assert SAMPLE_A in audit
    assert SAMPLE_B in audit
    assert SAMPLE_C in audit
    assert DOMAIN_ASCII in audit
    assert len(re.findall(r"seed_hex=[0-9a-f]{8}", audit)) >= 3
    assert len(re.findall(r"sk_hex=[0-9a-f]{64}", audit)) >= 3
    assert len(re.findall(r"pubkey_hex=[0-9a-f]{64}", audit)) >= 3
    assert len(re.findall(r"sig_hex=[0-9a-f]{128}", audit)) >= 3
    assert len(re.findall(r"message_hex=[0-9a-f]+", audit)) >= 3
    assert "key_dom_hex=" in audit
