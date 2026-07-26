"""Verifier for SoftHSM JCE trust rebind admission."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

OUTPUT = Path("/output/sign-ledger.json")
QUARANTINE = Path("/output/quarantine.json")
FIXTURES = Path("/app/data/fixtures")
SURFACE = FIXTURES / "surface_attestation.json"
SEED = FIXTURES / "seed.json"
SEGMENTS = Path("/app/data/signed_segments")
VERIFIER_OUT = Path("/tmp") / "sign-ledger-verify.json"
DYNAMIC_OUT = Path("/tmp") / "sign-ledger-dynamic.json"
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
    (20, "lora", 1400),
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
SCHEMA_VERSION = 1
EPOCH_TEN = 10
EPOCH_FIFTEEN = 15
EPOCH_TWENTY = 20
EPOCH_TWENTY_FIVE = 25
EPOCH_THIRTY = 30
EPOCH_FORTY = 40
EPOCH_FIFTY = 50
NEAR_MISS = 1
KEY_BACKENDS = "backends"
KEY_EPOCHS = "epochs"
KEY_REJECTED = "rejected"
REASON_INTEGRITY = "integrity_failure"
REASON_REPLAY = "replay"
REASON_REVOKED = "revoked"
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
PROFILE_A = "fleet_a"
PROFILE_B = "fleet_b"
BACKEND_NAMES = {"mqtt", "lora", "uart", "canbus", "zigbee"}
KEY_EPOCH = "epoch"
KEY_LANE = "lane"
KEY_TS = "ts"
SAMPLE_A = "sample_a"
SAMPLE_E = "sample_e"


def _accepted_in_band(got: int, expected: int) -> None:
    """Near-miss band: allow one over-reject; never allow +1 inflation."""
    assert expected - NEAR_MISS <= got <= expected


def _quarantine_path_for(attest_out: Path) -> Path:
    name = attest_out.name.replace("sign-ledger", "quarantine")
    return attest_out.with_name(name)


def _rebuild_and_attest(out: Path) -> dict:
    result = subprocess.run(
        ["cargo", "build", "-p", "trusteval", "--release"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"cargo build failed:\n{result.stderr}"
    result = subprocess.run(
        ["/app/target/release/trusteval", "attest", "--out", str(out)],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"trusteval attest failed:\n{result.stderr}"
    body = out.read_text(encoding="utf-8")
    data = json.loads(body)
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
        for e in data[KEY_REJECTED]
        if e["reason"] == reason
    }


@pytest.fixture(scope="module")
def roster_from_binary() -> dict:
    """Fresh rebuild + attestation from current /app sources."""
    return _rebuild_and_attest(VERIFIER_OUT)


@pytest.fixture(scope="module")
def quarantine_from_binary(roster_from_binary: dict) -> dict:
    """Quarantine produced by the same rebuild as roster_from_binary."""
    _ = roster_from_binary
    return _load_quarantine(_quarantine_path_for(VERIFIER_OUT))


def _status_map(roster: dict) -> dict[str, str]:
    assert roster.get("version") == SCHEMA_VERSION
    backends = roster[KEY_BACKENDS]
    return {row["name"]: row["status"] for row in backends}


def _epoch_map(roster: dict) -> dict[int, dict]:
    return {int(row["id"]): row for row in roster[KEY_EPOCHS]}


def test_roster_structure(roster_from_binary: dict):
    """Attestation shape plus deep-path signal (not surface-inflated epoch 10)."""
    assert roster_from_binary["version"] == SCHEMA_VERSION
    assert KEY_BACKENDS in roster_from_binary
    assert KEY_EPOCHS in roster_from_binary
    backends = roster_from_binary[KEY_BACKENDS]
    assert len(backends) == 5
    names = {b["name"] for b in backends}
    assert names == BACKEND_NAMES
    for b in backends:
        assert b["status"] in (STATUS_ACTIVE, STATUS_INACTIVE)
    epochs = _epoch_map(roster_from_binary)
    assert {EPOCH_TEN, EPOCH_TWENTY, EPOCH_FORTY, EPOCH_FIFTY}.issubset(epochs.keys())
    assert int(epochs[EPOCH_TEN]["accepted"]) < SURFACE_EPOCH_10
    assert int(epochs[EPOCH_TEN]["accepted"]) >= 3


def test_authority_correct_tier(roster_from_binary: dict):
    """Epoch 10 deep tally is in the restored band (exact restore is a harder gate)."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_TEN in epochs
    accepted_10 = int(epochs[EPOCH_TEN]["accepted"])
    assert 5 <= accepted_10 <= 8
    assert accepted_10 < SURFACE_EPOCH_10


def test_keyed_integrity_rejects_injected(roster_from_binary: dict):
    """Forged frames must not inflate epoch 10 accepted above the deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 5 <= int(epochs[EPOCH_TEN]["accepted"]) <= 8
    assert int(epochs[EPOCH_TEN]["accepted"]) < SURFACE_EPOCH_10


def test_keyed_integrity_epoch30(roster_from_binary: dict):
    """Epoch 30 remains published under hold co-presence with reduced tally."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_THIRTY in epochs
    accepted = int(epochs[EPOCH_THIRTY]["accepted"])
    assert 2 <= accepted <= 4
    assert accepted < 6


def test_keyed_integrity_epoch40(roster_from_binary: dict):
    """Epoch 40 accepted is in the restored deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 4 <= int(epochs[EPOCH_FORTY]["accepted"]) <= 6


def test_replay_detection_epoch10(roster_from_binary: dict):
    """Epoch 10 rejects enough replays to stay in the deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 5 <= int(epochs[EPOCH_TEN]["accepted"]) <= 8


def test_replay_detection_epoch20(roster_from_binary: dict):
    """Epoch 20 rejects enough replays/revokes to stay in the deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 3 <= int(epochs[EPOCH_TWENTY]["accepted"]) <= 6


def test_replay_detection_epoch50(roster_from_binary: dict):
    """Epoch 50 accepted is in the restored deep band."""
    epochs = _epoch_map(roster_from_binary)
    assert 3 <= int(epochs[EPOCH_FIFTY]["accepted"]) <= 5


def test_revocation_epoch20(roster_from_binary: dict):
    """Epoch 20 reflects ledger revocation (band; exact count is a harder gate)."""
    epochs = _epoch_map(roster_from_binary)
    assert 3 <= int(epochs[EPOCH_TWENTY]["accepted"]) <= 6


def test_hold_semantics_epoch30(roster_from_binary: dict):
    """Epoch 30 publishes with held co-presence (exact restored accepted)."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_THIRTY in epochs
    assert epochs[EPOCH_THIRTY]["profile"] == PROFILE_A
    assert int(epochs[EPOCH_THIRTY]["accepted"]) == EPOCH_30_ACCEPTED


def test_copresence_backends(roster_from_binary: dict):
    """Matrix lanes active; off-matrix inactive; deep path not surface-inflated."""
    statuses = _status_map(roster_from_binary)
    assert statuses.get("mqtt") == STATUS_ACTIVE
    assert statuses.get("lora") == STATUS_ACTIVE
    assert statuses.get("uart") == STATUS_ACTIVE
    assert statuses.get("canbus") == STATUS_INACTIVE
    assert statuses.get("zigbee") == STATUS_INACTIVE
    epochs = _epoch_map(roster_from_binary)
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    surface_epochs = {int(e["id"]): e for e in surface[KEY_EPOCHS]}
    assert int(epochs[EPOCH_TEN]["accepted"]) < int(surface_epochs[EPOCH_TEN]["accepted"])
    assert int(epochs[EPOCH_TWENTY]["accepted"]) < int(surface_epochs[EPOCH_TWENTY]["accepted"])


def test_all_epochs_present(roster_from_binary: dict):
    """Fleet epochs publish with correct profiles (including novel epoch 15)."""
    epochs = _epoch_map(roster_from_binary)
    assert {EPOCH_TEN, EPOCH_FIFTEEN, EPOCH_TWENTY, EPOCH_THIRTY, EPOCH_FORTY, EPOCH_FIFTY}.issubset(epochs.keys())
    assert epochs[EPOCH_TEN]["profile"] == PROFILE_A
    assert epochs[EPOCH_FIFTEEN]["profile"] == PROFILE_A
    assert 2 <= int(epochs[EPOCH_FIFTEEN]["accepted"]) <= 4
    assert epochs[EPOCH_TWENTY]["profile"] == PROFILE_A
    assert epochs[EPOCH_THIRTY]["profile"] == PROFILE_A
    assert epochs[EPOCH_FORTY]["profile"] == PROFILE_B
    assert epochs[EPOCH_FIFTY]["profile"] == PROFILE_B


def test_revoked_lane_omits_epoch(roster_from_binary: dict):
    """Epoch with a required lane only-revoked must not publish."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_TWENTY_FIVE not in epochs
    assert EPOCH_TEN in epochs and EPOCH_TWENTY in epochs and EPOCH_THIRTY in epochs


def test_hold_keeps_epoch_with_reduced_accepted(roster_from_binary: dict):
    """Hold co-presence keeps the epoch; accepted is only non-held trust."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_THIRTY in epochs
    assert epochs[EPOCH_THIRTY]["profile"] == PROFILE_A
    assert int(epochs[EPOCH_THIRTY]["accepted"]) == EPOCH_30_ACCEPTED
    assert int(epochs[EPOCH_THIRTY]["accepted"]) < 6


def test_output_differs_from_surface(roster_from_binary: dict):
    """Deep attestation must disagree with the surface fixture on shared epochs."""
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert roster_from_binary != surface
    surface_epochs = {int(e["id"]): e for e in surface[KEY_EPOCHS]}
    roster_epochs = _epoch_map(roster_from_binary)
    for eid in (EPOCH_TEN, EPOCH_TWENTY, EPOCH_FORTY, EPOCH_FIFTY):
        assert eid in roster_epochs
        assert int(roster_epochs[eid]["accepted"]) < int(surface_epochs[eid]["accepted"])


def test_output_matches_rebuilt(roster_from_binary: dict):
    """On-disk agent output must match rebuilt trusteval with exact epoch-10 restore."""
    assert OUTPUT.is_file(), f"missing {OUTPUT}"
    on_disk = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert on_disk == roster_from_binary
    epochs = _epoch_map(on_disk)
    assert int(epochs[EPOCH_TEN]["accepted"]) == EPOCH_10_ACCEPTED
    assert int(epochs[EPOCH_TWENTY]["accepted"]) == EPOCH_20_ACCEPTED


def test_attestation_stable_across_runs(roster_from_binary: dict):
    """Second attest run must match the first and stay below surface tallies."""
    second = _rebuild_and_attest(Path("/tmp") / "sign-ledger-second.json")
    assert second == roster_from_binary
    epochs = _epoch_map(second)
    assert int(epochs[EPOCH_TEN]["accepted"]) < SURFACE_EPOCH_10
    assert EPOCH_THIRTY in epochs


def test_output_differs_from_surfcheck(roster_from_binary: dict):
    """Agent output must differ from surfcheck and beat surface inflation."""
    surface_poke = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert roster_from_binary != surface_poke
    assert OUTPUT.is_file()
    on_disk = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert on_disk == roster_from_binary
    assert on_disk != surface_poke
    assert Path("/app/bin").joinpath("surfcheck").is_file()
    assert Path("/app/bin").joinpath("framecheck").is_file()
    epochs = _epoch_map(on_disk)
    poke_epochs = {int(e["id"]): e for e in surface_poke[KEY_EPOCHS]}
    assert int(epochs[EPOCH_TEN]["accepted"]) < int(poke_epochs[EPOCH_TEN]["accepted"])


def test_dynamic_frame_injection():
    """Inject a valid novel-epoch frame; hardcoded audit materials must not suffice."""
    seg_path = SEGMENTS / "seg_99.bin"
    assert DYNAMIC_FRAME.is_file(), "dynamic test frame fixture missing"
    shutil.copy(DYNAMIC_FRAME, seg_path)
    try:
        roster = _rebuild_and_attest(DYNAMIC_OUT)
        epochs = _epoch_map(roster)
        assert int(epochs[EPOCH_FIFTEEN]["accepted"]) == EPOCH_15_ACCEPTED + 1, (
            f"Expected {EPOCH_15_ACCEPTED + 1} after injection, got {epochs[EPOCH_FIFTEEN]['accepted']}"
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
        assert 4 <= int(epochs[EPOCH_FORTY]["accepted"]) <= 6, (
            f"Expected epoch 40 in [4,6] after forged inject, got {epochs[EPOCH_FORTY]['accepted']}"
        )
    finally:
        seg_path.unlink(missing_ok=True)


def test_quarantine_structure(
    roster_from_binary: dict, quarantine_from_binary: dict
):
    """Quarantine shape and reason vocabulary match rebuilt trusteval."""
    _ = roster_from_binary
    assert QUARANTINE.is_file(), f"missing {QUARANTINE}"
    agent = _load_quarantine(QUARANTINE)
    assert len(agent[KEY_REJECTED]) == len(quarantine_from_binary[KEY_REJECTED])
    reasons = {e["reason"] for e in agent[KEY_REJECTED]}
    assert REASON_INTEGRITY in reasons
    assert REASON_REPLAY in reasons
    assert REASON_REVOKED in reasons
    for entry in agent[KEY_REJECTED]:
        assert KEY_EPOCH in entry
        assert KEY_LANE in entry
        assert KEY_TS in entry
        assert entry["reason"] in (REASON_INTEGRITY, REASON_REPLAY, REASON_REVOKED)


def test_quarantine_integrity_failures(
    roster_from_binary: dict, quarantine_from_binary: dict
):
    """integrity_failure rows match the rebuilt oracle set."""
    _ = roster_from_binary
    agent = _load_quarantine(QUARANTINE)
    assert _reason_keys(agent, REASON_INTEGRITY) == _reason_keys(
        quarantine_from_binary, "integrity_failure"
    )
    assert len(_reason_keys(agent, REASON_INTEGRITY)) == INTEGRITY_FAILURE_COUNT
    assert CORE_INTEGRITY.issubset(_reason_keys(agent, REASON_INTEGRITY))


def test_quarantine_replay_entries(
    roster_from_binary: dict, quarantine_from_binary: dict
):
    """replay rows match the rebuilt oracle set."""
    _ = roster_from_binary
    agent = _load_quarantine(QUARANTINE)
    assert _reason_keys(agent, REASON_REPLAY) == _reason_keys(
        quarantine_from_binary, "replay"
    )
    assert len(_reason_keys(agent, REASON_REPLAY)) == REPLAY_COUNT
    assert len(CORE_REPLAYS & _reason_keys(agent, REASON_REPLAY)) >= 3


def test_quarantine_revoked_entries(
    roster_from_binary: dict, quarantine_from_binary: dict
):
    """revoked WAL rows match the rebuilt oracle set."""
    _ = roster_from_binary
    agent = _load_quarantine(QUARANTINE)
    assert _reason_keys(agent, REASON_REVOKED) == _reason_keys(
        quarantine_from_binary, "revoked"
    )
    assert len(_reason_keys(agent, REASON_REVOKED)) == REVOKED_COUNT
    assert _reason_keys(agent, REASON_REVOKED) == _reason_keys(
        quarantine_from_binary, REASON_REVOKED
    )


def test_exact_restore_counts(roster_from_binary: dict):
    """Full exact accepted restore across primary epochs (complete deep path)."""
    epochs = _epoch_map(roster_from_binary)
    assert int(epochs[EPOCH_TEN]["accepted"]) == EPOCH_10_ACCEPTED
    assert int(epochs[EPOCH_FIFTEEN]["accepted"]) == EPOCH_15_ACCEPTED
    assert int(epochs[EPOCH_TWENTY]["accepted"]) == EPOCH_20_ACCEPTED
    assert int(epochs[EPOCH_THIRTY]["accepted"]) == EPOCH_30_ACCEPTED
    assert int(epochs[EPOCH_FORTY]["accepted"]) == EPOCH_40_ACCEPTED
    assert int(epochs[EPOCH_FIFTY]["accepted"]) == EPOCH_50_ACCEPTED


def test_exact_quarantine_integrity_set(
    roster_from_binary: dict, quarantine_from_binary: dict
):
    """Exact integrity quarantine set matches rebuild (complete keyed schedule)."""
    _ = roster_from_binary
    agent = _load_quarantine(QUARANTINE)
    assert _reason_keys(agent, REASON_INTEGRITY) == _reason_keys(
        quarantine_from_binary, "integrity_failure"
    )
    assert _reason_keys(agent, REASON_INTEGRITY) == EXPECTED_INTEGRITY


def test_quarantine_matches_rebuilt(
    roster_from_binary: dict, quarantine_from_binary: dict
):
    """On-disk quarantine equals rebuilt trusteval quarantine."""
    _ = roster_from_binary
    agent = _load_quarantine(QUARANTINE)
    assert agent == quarantine_from_binary


def test_fixtures_untouched():
    """Fixtures stay shipped; deep publish must exist (no free pass on timeout-only)."""
    assert OUTPUT.is_file(), "missing /output/sign-ledger.json"
    assert QUARANTINE.is_file(), "missing /output/quarantine.json"
    data = json.loads(SEED.read_text(encoding="utf-8"))
    assert data.get("seed") == "lane-lattice-v2"
    assert data.get("preserve") is True
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert surface.get("version") == SCHEMA_VERSION
    assert int(surface[KEY_EPOCHS][0]["accepted"]) == 10
    audit = (FIXTURES / "pre_incident_audit.log").read_text(encoding="utf-8")
    assert SAMPLE_A in audit
    assert SAMPLE_E in audit
    assert "domain_ascii=SHSM" in audit
    assert "material_hex=" not in audit
    assert len(re.findall(r"seed_hex=[0-9a-f]{8}", audit)) >= 5
    assert len(re.findall(r"message_hex=[0-9a-f]+", audit)) >= 5
    assert len(re.findall(r"sk_hex=[0-9a-f]{64}", audit)) >= 5
    # Sealed framecheck only — no probe/tools_src tree under /app.
    assert Path("/app/bin/framecheck").is_file()


def test_durable_preference_survives_rebuild(roster_from_binary: dict):
    """Live surface prefer must not remain; durable authority is required for deep rebuilds."""
    _ = roster_from_binary
    prefer = (Path("/app/ops") / "prefer.toml").read_text(encoding="utf-8")
    assert 'root = "durable"' in prefer
    assert 'bind = "authority"' in prefer
    # Preference must remain durable across a second verifier rebuild.
    second = _rebuild_and_attest(Path("/tmp") / "sign-ledger-prefer.json")
    assert _epoch_map(second) == _epoch_map(roster_from_binary)
