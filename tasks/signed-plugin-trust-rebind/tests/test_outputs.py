"""Verifier for signed-plugin trust rebind admission."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

OUTPUT = Path("/output/plugin-ledger.json")
QUARANTINE = Path("/output/quarantine.json")
FIXTURES = Path("/app/data/fixtures")
SURFACE = FIXTURES / "surface_attestation.json"
SEED = FIXTURES / "seed.json"
SEGMENTS = Path("/app/data/signed_segments")
VERIFIER_OUT = Path("/tmp") / "plugin-ledger-verify.json"
DYNAMIC_OUT = Path("/tmp") / "plugin-ledger-dynamic.json"
DYNAMIC_FRAME = FIXTURES / "dynamic_test_frame.bin"
DYNAMIC_INJECTED = FIXTURES / "dynamic_test_injected.bin"

EPOCH_10_ACCEPTED = 7
EPOCH_15_ACCEPTED = 3
EPOCH_20_ACCEPTED = 5
EPOCH_30_ACCEPTED = 3
EPOCH_40_ACCEPTED = 5
EPOCH_50_ACCEPTED = 4
INTEGRITY_FAILURE_COUNT = 13
REPLAY_COUNT = 5
REVOKED_COUNT = 1
# Critical integrity failures every deep path must catch (subset; full set is harder).
CORE_INTEGRITY = {
    (10, "lora", 850),
    (10, "mqtt", 920),
    (20, "mqtt", 1900),
    (30, "lora", 720),
    (40, "uart", 1350),
    (50, "uart", 1150),
}
CORE_REPLAYS = {
    (10, "mqtt", 810),
    (20, "lora", 1100),
    (40, "uart", 1050),
    (50, "uart", 900),
}
EXPECTED_INTEGRITY = CORE_INTEGRITY | {
    (10, "mqtt", 960),
    (15, "lora", 650),
    (20, "lora", 1700),
    (20, "mqtt", 1850),
    (30, "lora", 780),
    (40, "uart", 1420),
    (50, "uart", 1050),
}
SURFACE_EPOCH_10 = 10


def _rebuild_and_attest(out: Path) -> dict:
    result = subprocess.run(
        ["cargo", "build", "-p", "trusteval", "--release"],
        cwd="/app",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"cargo build failed:\n{result.stderr}"
    result = subprocess.run(
        ["/app/target/release/trusteval", "attest", "--out", str(out)],
        cwd="/app",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"trusteval attest failed:\n{result.stderr}"
    body = out.read_text(encoding="utf-8")
    data = json.loads(body)
    assert data.get("version") == 1
    return data


@pytest.fixture(scope="module")
def roster_from_binary() -> dict:
    """Fresh rebuild + attestation from current /app sources."""
    return _rebuild_and_attest(VERIFIER_OUT)


def _status_map(roster: dict) -> dict[str, str]:
    assert roster.get("version") == 1
    backends = roster["backends"]
    return {row["name"]: row["status"] for row in backends}


def _epoch_map(roster: dict) -> dict[int, dict]:
    return {int(row["id"]): row for row in roster["epochs"]}


def test_roster_structure(roster_from_binary: dict):
    """Attestation shape plus deep-path signal (not surface-inflated epoch 10)."""
    assert roster_from_binary["version"] == 1
    assert "backends" in roster_from_binary
    assert "epochs" in roster_from_binary
    backends = roster_from_binary["backends"]
    assert len(backends) == 5
    names = {b["name"] for b in backends}
    assert names == {"mqtt", "lora", "uart", "canbus", "zigbee"}
    for b in backends:
        assert b["status"] in ("active", "inactive")
    epochs = _epoch_map(roster_from_binary)
    assert {10, 15, 20, 40, 50}.issubset(epochs.keys())
    assert int(epochs[10]["accepted"]) < SURFACE_EPOCH_10
    assert 5 <= int(epochs[10]["accepted"]) <= 8


def test_authority_correct_tier(roster_from_binary: dict):
    """Epoch 10 deep tally is in the restored band (exact restore is a harder gate)."""
    epochs = _epoch_map(roster_from_binary)
    assert 10 in epochs
    accepted_10 = int(epochs[10]["accepted"])
    assert 5 <= accepted_10 <= 8
    assert accepted_10 < SURFACE_EPOCH_10


def test_keyed_integrity_rejects_injected(roster_from_binary: dict):
    """Forged frames must not inflate epoch 10 accepted above the deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 5 <= int(epochs[10]["accepted"]) <= 8
    assert int(epochs[10]["accepted"]) < SURFACE_EPOCH_10


def test_keyed_integrity_epoch30(roster_from_binary: dict):
    """Epoch 30 remains published under hold co-presence with reduced tally."""
    epochs = _epoch_map(roster_from_binary)
    assert 30 in epochs
    accepted = int(epochs[30]["accepted"])
    assert 2 <= accepted <= 4
    assert accepted < 6


def test_keyed_integrity_epoch40(roster_from_binary: dict):
    """Epoch 40 accepted is in the restored deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 4 <= int(epochs[40]["accepted"]) <= 6


def test_replay_detection_epoch10(roster_from_binary: dict):
    """Epoch 10 rejects enough replays to stay in the deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 5 <= int(epochs[10]["accepted"]) <= 8


def test_replay_detection_epoch20(roster_from_binary: dict):
    """Epoch 20 rejects enough replays/revokes to stay in the deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 3 <= int(epochs[20]["accepted"]) <= 6
    # Must not leave the classic WAL replay out of quarantine.
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    replay_keys = {
        (e["epoch"], e["lane"], e["ts"])
        for e in data["rejected"]
        if e["reason"] == "replay"
    }
    assert (20, "lora", 1100) in replay_keys


def test_replay_detection_epoch50(roster_from_binary: dict):
    """Epoch 50 accepted is in the restored deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 3 <= int(epochs[50]["accepted"]) <= 5


def test_revocation_epoch20(roster_from_binary: dict):
    """Epoch 20 reflects ledger revocation (band; exact count is a harder gate)."""
    epochs = _epoch_map(roster_from_binary)
    assert 3 <= int(epochs[20]["accepted"]) <= 6
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    revoked_keys = {
        (e["epoch"], e["lane"], e["ts"])
        for e in data["rejected"]
        if e["reason"] == "revoked"
    }
    assert (20, "lora", 1600) in revoked_keys


def test_hold_semantics_epoch30(roster_from_binary: dict):
    """Epoch 30 publishes with held co-presence (band; exact tally is a harder gate)."""
    epochs = _epoch_map(roster_from_binary)
    assert 30 in epochs
    assert epochs[30]["profile"] == "fleet_a"
    assert 2 <= int(epochs[30]["accepted"]) <= 4


def test_copresence_backends(roster_from_binary: dict):
    """Matrix lanes active; off-matrix inactive; deep path not surface-inflated."""
    statuses = _status_map(roster_from_binary)
    assert statuses.get("mqtt") == "active"
    assert statuses.get("lora") == "active"
    assert statuses.get("uart") == "active"
    assert statuses.get("canbus") == "inactive"
    assert statuses.get("zigbee") == "inactive"
    epochs = _epoch_map(roster_from_binary)
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    surface_epochs = {int(e["id"]): e for e in surface["epochs"]}
    assert 5 <= int(epochs[10]["accepted"]) <= 8
    assert int(epochs[10]["accepted"]) < int(surface_epochs[10]["accepted"])
    assert int(epochs[20]["accepted"]) < int(surface_epochs[20]["accepted"])
    # Credential JSONL must contribute: WAL-only undercounts epoch 10 below 5.
    assert int(epochs[10]["accepted"]) >= 5


def test_all_epochs_present(roster_from_binary: dict):
    """Fleet epochs publish with correct profiles (including novel epoch 15)."""
    epochs = _epoch_map(roster_from_binary)
    assert {10, 15, 20, 30, 40, 50}.issubset(epochs.keys())
    assert epochs[10]["profile"] == "fleet_a"
    assert epochs[15]["profile"] == "fleet_a"
    assert 2 <= int(epochs[15]["accepted"]) <= 4
    assert epochs[20]["profile"] == "fleet_a"
    assert epochs[30]["profile"] == "fleet_a"
    assert epochs[40]["profile"] == "fleet_b"
    assert epochs[50]["profile"] == "fleet_b"


def test_revoked_lane_omits_epoch(roster_from_binary: dict):
    """Epoch with a required lane only-revoked must not publish."""
    epochs = _epoch_map(roster_from_binary)
    assert 25 not in epochs
    assert 10 in epochs and 20 in epochs and 30 in epochs


def test_hold_keeps_epoch_with_reduced_accepted(roster_from_binary: dict):
    """Suspended co-presence keeps the epoch; accepted stays below a full lane set."""
    epochs = _epoch_map(roster_from_binary)
    assert 30 in epochs
    assert epochs[30]["profile"] == "fleet_a"
    assert 2 <= int(epochs[30]["accepted"]) <= 4
    assert int(epochs[30]["accepted"]) < 6


def test_output_differs_from_surface(roster_from_binary: dict):
    """Deep attestation must disagree with the surface fixture on shared epochs."""
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert roster_from_binary != surface
    surface_epochs = {int(e["id"]): e for e in surface["epochs"]}
    roster_epochs = _epoch_map(roster_from_binary)
    for eid in (10, 20, 40, 50):
        assert eid in roster_epochs
        assert int(roster_epochs[eid]["accepted"]) < int(surface_epochs[eid]["accepted"])
    # Require a meaningful gap on epoch 10 (not just any inequality).
    assert int(surface_epochs[10]["accepted"]) - int(roster_epochs[10]["accepted"]) >= 2


def test_output_matches_rebuilt(roster_from_binary: dict):
    """On-disk agent output must match rebuilt trusteval with exact epoch-10 restore."""
    assert OUTPUT.is_file(), f"missing {OUTPUT}"
    on_disk = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert on_disk == roster_from_binary
    epochs = _epoch_map(on_disk)
    assert int(epochs[10]["accepted"]) == EPOCH_10_ACCEPTED
    assert int(epochs[20]["accepted"]) == EPOCH_20_ACCEPTED


def test_attestation_stable_across_runs(roster_from_binary: dict):
    """Second attest run must match the first and stay below surface tallies."""
    second = _rebuild_and_attest(Path("/tmp") / "plugin-ledger-second.json")
    assert second == roster_from_binary
    epochs = _epoch_map(second)
    assert int(epochs[10]["accepted"]) < SURFACE_EPOCH_10
    assert 30 in epochs
    assert 2 <= int(epochs[30]["accepted"]) <= 4


def test_output_differs_from_jarcheck(roster_from_binary: dict):
    """Agent output must differ from jarcheck and beat surface inflation."""
    surface_poke = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert roster_from_binary != surface_poke
    assert OUTPUT.is_file()
    on_disk = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert on_disk == roster_from_binary
    assert on_disk != surface_poke
    assert Path("/app/bin").joinpath("jarcheck").is_file()
    assert Path("/app/bin").joinpath("framecheck").is_file()
    epochs = _epoch_map(on_disk)
    poke_epochs = {int(e["id"]): e for e in surface_poke["epochs"]}
    assert int(epochs[10]["accepted"]) < int(poke_epochs[10]["accepted"])
    assert 5 <= int(epochs[10]["accepted"]) <= 8


def test_dynamic_frame_injection():
    """Inject a valid novel-epoch frame; hardcoded audit materials must not suffice."""
    seg_path = SEGMENTS / "seg_99.bin"
    assert DYNAMIC_FRAME.is_file(), "dynamic test frame fixture missing"
    shutil.copy(DYNAMIC_FRAME, seg_path)
    try:
        roster = _rebuild_and_attest(DYNAMIC_OUT)
        epochs = _epoch_map(roster)
        assert int(epochs[15]["accepted"]) == EPOCH_15_ACCEPTED + 1, (
            f"Expected {EPOCH_15_ACCEPTED + 1} after injection, got {epochs[15]['accepted']}"
        )
    finally:
        seg_path.unlink(missing_ok=True)


def test_dynamic_injected_frame_rejected():
    """Inject a forged frame and verify it is rejected (band on epoch 40)."""
    seg_path = SEGMENTS / "seg_98.bin"
    assert DYNAMIC_INJECTED.is_file(), "dynamic injected frame fixture missing"
    shutil.copy(DYNAMIC_INJECTED, seg_path)
    try:
        roster = _rebuild_and_attest(DYNAMIC_OUT)
        epochs = _epoch_map(roster)
        assert 4 <= int(epochs[40]["accepted"]) <= 6, (
            f"Expected epoch 40 in [4,6] after forged inject, got {epochs[40]['accepted']}"
        )
    finally:
        seg_path.unlink(missing_ok=True)


def test_quarantine_structure(roster_from_binary: dict):
    """Quarantine lists rejected credentials with required reason vocabulary."""
    assert QUARANTINE.is_file(), f"missing {QUARANTINE}"
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    assert data.get("version") == 1
    assert "rejected" in data
    rejected = data["rejected"]
    assert len(rejected) >= 8, f"Expected at least 8 rejected frames, got {len(rejected)}"
    reasons = {e["reason"] for e in rejected}
    assert "integrity_failure" in reasons
    assert "replay" in reasons
    assert "revoked" in reasons
    for entry in rejected:
        assert "epoch" in entry
        assert "lane" in entry
        assert "ts" in entry
        assert entry["reason"] in ("integrity_failure", "replay", "revoked")


def test_quarantine_integrity_failures(roster_from_binary: dict):
    """Quarantine catches core integrity failures; full exact set remains a harder gate."""
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    integrity_failures = [e for e in data["rejected"] if e["reason"] == "integrity_failure"]
    assert 8 <= len(integrity_failures) <= 20
    failure_keys = {(e["epoch"], e["lane"], e["ts"]) for e in integrity_failures}
    assert CORE_INTEGRITY.issubset(failure_keys)


def test_quarantine_replay_entries(roster_from_binary: dict):
    """Quarantine contains core replay entries for non-advancing streams."""
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    replays = [e for e in data["rejected"] if e["reason"] == "replay"]
    assert 3 <= len(replays) <= 8
    replay_keys = {(e["epoch"], e["lane"], e["ts"]) for e in replays}
    hit = len(CORE_REPLAYS & replay_keys)
    assert hit >= 3, f"Expected >=3 core replays, got {hit} from {replay_keys}"


def test_quarantine_revoked_entries(roster_from_binary: dict):
    """Quarantine lists revoked WAL frames only (not credential JSONL revokes)."""
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    revoked = [e for e in data["rejected"] if e["reason"] == "revoked"]
    assert len(revoked) >= 1
    revoked_keys = {(e["epoch"], e["lane"], e["ts"]) for e in revoked}
    assert (20, "lora", 1600) in revoked_keys
    assert (20, "lora", 1800) not in revoked_keys


def test_exact_restore_counts(roster_from_binary: dict):
    """Full exact accepted restore across primary epochs (complete deep path)."""
    epochs = _epoch_map(roster_from_binary)
    assert int(epochs[10]["accepted"]) == EPOCH_10_ACCEPTED
    assert int(epochs[15]["accepted"]) == EPOCH_15_ACCEPTED
    assert int(epochs[20]["accepted"]) == EPOCH_20_ACCEPTED
    assert int(epochs[30]["accepted"]) == EPOCH_30_ACCEPTED
    assert int(epochs[40]["accepted"]) == EPOCH_40_ACCEPTED
    assert int(epochs[50]["accepted"]) == EPOCH_50_ACCEPTED


def test_exact_quarantine_integrity_set(roster_from_binary: dict):
    """Exact integrity quarantine set (complete keyed schedule)."""
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    integrity_failures = [e for e in data["rejected"] if e["reason"] == "integrity_failure"]
    assert len(integrity_failures) == INTEGRITY_FAILURE_COUNT
    failure_keys = {(e["epoch"], e["lane"], e["ts"]) for e in integrity_failures}
    assert failure_keys == EXPECTED_INTEGRITY
    # Capture-order replay on epoch 40 must also be present for a full restore.
    replays = {
        (e["epoch"], e["lane"], e["ts"])
        for e in data["rejected"]
        if e["reason"] == "replay"
    }
    assert (40, "uart", 1050) in replays


def test_fixtures_untouched():
    """Fixtures stay shipped; deep publish must exist and beat surface inflation."""
    assert OUTPUT.is_file(), "missing /output/plugin-ledger.json"
    assert QUARANTINE.is_file(), "missing /output/quarantine.json"
    data = json.loads(SEED.read_text(encoding="utf-8"))
    assert data.get("seed") == "lane-lattice-v2"
    assert data.get("preserve") is True
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert surface.get("version") == 1
    assert int(surface["epochs"][0]["accepted"]) == 10
    on_disk = json.loads(OUTPUT.read_text(encoding="utf-8"))
    epochs = _epoch_map(on_disk)
    assert 5 <= int(epochs[10]["accepted"]) <= 8
    assert int(epochs[10]["accepted"]) < int(surface["epochs"][0]["accepted"])
    audit = (FIXTURES / "pre_incident_audit.log").read_text(encoding="utf-8")
    assert "sample_1" in audit
    assert "sample_5" in audit
    assert "material_hex=" not in audit
    assert len(re.findall(r"seed_hex=[0-9a-f]{8}", audit)) >= 5
    assert len(re.findall(r"check=0x[0-9a-f]{2}", audit)) >= 5
    # Probe source must not be installed under /app (sealed binary only).
    assert not Path("/app/probe").exists()
