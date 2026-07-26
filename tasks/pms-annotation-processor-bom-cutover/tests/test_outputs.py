"""Verifier for companion mesh trust attestation recovery."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

OUTPUT = Path("/output/mesh-attestation.json")
QUARANTINE = Path("/output/reject-ledger.json")
FIXTURES = Path("/app/data/fixtures")
SURFACE = FIXTURES / "surface_attestation.json"
SEED = FIXTURES / "seed.json"
SEGMENTS = Path("/app/data/signed_segments")
VERIFIER_OUT = Path("/tmp") / "mesh-attestation-verify.json"
DYNAMIC_OUT = Path("/tmp") / "mesh-attestation-dynamic.json"
DYNAMIC_FRAME = FIXTURES / "dynamic_test_frame.bin"
DYNAMIC_INJECTED = FIXTURES / "dynamic_test_injected.bin"

EPOCH_10_ACCEPTED = 7
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
REASON_SEAL = "seal_break"
REASON_REPLAY = "replay"
REASON_REVOKED = "revoked"
QUARANTINE_REASONS = (REASON_SEAL, REASON_REPLAY, REASON_REVOKED)
KEY_BACKENDS = "backends"
KEY_EPOCHS = "epochs"
KEY_REJECTED = "rejected"
EPOCH_TEN = 10
EPOCH_TWENTY = 20
EPOCH_THIRTY = 30
EPOCH_FORTY = 40
EPOCH_FIFTY = 50
EPOCH_TWENTY_FIVE = 25
BAND_LO = 2
BAND_HI = 4
BAND_CAP = 6
BACKEND_COUNT = 5
MIN_REJECTED = 10
MIN_SEAL_BREAKS = 5
MIN_REPLAYS = 4
MIN_REVOKED = 1
EXPECTED_REPLAY_KEYS = {
    (10, "mqtt", 810),
    (20, "lora", 1400),
    (20, "lora", 1100),
    (40, "uart", 1050),
    (50, "uart", 900),
}
SAMPLE_A = "sample_a"
SAMPLE_B = "sample_b"
SEED_NAME = "lane-lattice-v2"
SURFSKIM_BIN = "surfskim"


def _reject_path_for(attest_out: Path) -> Path:
    name = attest_out.name.replace("mesh-attestation", "reject-ledger")
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


def _load_reject_ledger(path: Path) -> dict:
    assert path.is_file(), f"missing reject ledger at {path}"
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


@pytest.fixture(scope="module")
def roster_from_binary() -> dict:
    """Fresh rebuild + attestation from current /app sources."""
    return _rebuild_and_attest(VERIFIER_OUT)


@pytest.fixture(scope="module")
def reject_from_binary(roster_from_binary: dict) -> dict:
    """Reject ledger produced by the same rebuild as roster_from_binary."""
    _ = roster_from_binary
    return _load_reject_ledger(_reject_path_for(VERIFIER_OUT))


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
    assert len(backends) == BACKEND_COUNT
    names = {b["name"] for b in backends}
    assert names == BACKEND_NAMES
    for b in backends:
        assert b["status"] in (STATUS_ACTIVE, STATUS_INACTIVE)
    epochs = _epoch_map(roster_from_binary)
    assert CORE_EPOCHS.issubset(epochs.keys())
    assert int(epochs[EPOCH_TEN]["accepted"]) < SURFACE_EPOCH_10
    assert int(epochs[EPOCH_TEN]["accepted"]) >= EPOCH_30_ACCEPTED


def test_authority_correct_tier(roster_from_binary: dict):
    """Surface-tier material does not control deep attestation."""
    leaf = Path("/app/data/manifests/tier_leaf.jsonl")
    backup = leaf.read_text(encoding="utf-8")
    out = Path("/tmp") / "mesh-attestation-leaf-blank.json"
    try:
        leaf.write_text("", encoding="utf-8")
        assert _rebuild_and_attest(out) == roster_from_binary
    finally:
        leaf.write_text(backup, encoding="utf-8")


def test_exact_restore_counts(roster_from_binary: dict):
    """A complete restore reproduces every deep accepted tally."""
    epochs = _epoch_map(roster_from_binary)
    assert {
        epoch: int(row["accepted"])
        for epoch, row in epochs.items()
    } == {
        EPOCH_TEN: EPOCH_10_ACCEPTED,
        EPOCH_TWENTY: EPOCH_20_ACCEPTED,
        EPOCH_THIRTY: EPOCH_30_ACCEPTED,
        EPOCH_FORTY: EPOCH_40_ACCEPTED,
        EPOCH_FIFTY: EPOCH_50_ACCEPTED,
    }


def test_keyed_integrity_rejects_injected(reject_from_binary: dict):
    """Forged base frames are classified as seal breaks."""
    failures = _reason_keys(reject_from_binary, REASON_SEAL)
    assert (EPOCH_TEN, "lora", 850) in failures
    assert (EPOCH_TEN, "mqtt", 920) in failures


def test_keyed_integrity_epoch30(roster_from_binary: dict):
    """Epoch 30 remains published under hold co-presence with reduced tally."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_THIRTY in epochs
    accepted = int(epochs[EPOCH_THIRTY]["accepted"])
    assert BAND_LO <= accepted <= BAND_HI
    assert accepted < BAND_CAP


def test_keyed_integrity_epoch40(reject_from_binary: dict):
    """Epoch 40 separates its forged frame from authentic WAL frames."""
    failures = _reason_keys(reject_from_binary, REASON_SEAL)
    assert (EPOCH_FORTY, "uart", 1350) in failures
    assert (EPOCH_FORTY, "uart", 1000) not in failures


def test_replay_detection_epoch10(reject_from_binary: dict):
    """Epoch 10 replay scope is the WAL stream, not credential rows."""
    replays = _reason_keys(reject_from_binary, REASON_REPLAY)
    assert (EPOCH_TEN, "mqtt", 810) in replays
    assert (EPOCH_TEN, "mqtt", 800) not in replays
    assert (EPOCH_TEN, "mqtt", 950) not in replays


def test_replay_detection_epoch20(reject_from_binary: dict):
    """Epoch 20 keeps advancing WAL frames below credential timestamps."""
    replays = _reason_keys(reject_from_binary, REASON_REPLAY)
    assert (EPOCH_TWENTY, "lora", 1100) in replays
    assert (EPOCH_TWENTY, "lora", 1200) not in replays
    assert (EPOCH_TWENTY, "lora", 1600) not in replays


def test_replay_detection_epoch50(reject_from_binary: dict):
    """Epoch 50 keeps its advancing WAL prefix before rejecting a replay."""
    replays = _reason_keys(reject_from_binary, REASON_REPLAY)
    assert (EPOCH_FIFTY, "uart", 900) in replays
    assert (EPOCH_FIFTY, "uart", 800) not in replays
    assert (EPOCH_FIFTY, "uart", 1100) not in replays


def test_revocation_epoch20(roster_from_binary: dict):
    """Epoch 20 reflects ledger revocation."""
    epochs = _epoch_map(roster_from_binary)
    assert int(epochs[EPOCH_TWENTY]["accepted"]) == EPOCH_20_ACCEPTED


def test_hold_semantics_epoch30(roster_from_binary: dict):
    """Epoch 30 publishes with held co-presence and a reduced tally."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_THIRTY in epochs
    assert epochs[EPOCH_THIRTY]["profile"] == PROFILE_A
    assert BAND_LO <= int(epochs[EPOCH_THIRTY]["accepted"]) <= BAND_HI


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
    assert int(epochs[EPOCH_TWENTY]["accepted"]) < int(
        surface_epochs[EPOCH_TWENTY]["accepted"]
    )


def test_all_epochs_present(roster_from_binary: dict):
    """All five fleet epochs publish with correct profiles."""
    epochs = _epoch_map(roster_from_binary)
    assert set(epochs.keys()) == PUBLISHED_EPOCHS
    assert epochs[EPOCH_TEN]["profile"] == PROFILE_A
    assert epochs[EPOCH_TWENTY]["profile"] == PROFILE_A
    assert epochs[EPOCH_THIRTY]["profile"] == PROFILE_A
    assert epochs[EPOCH_FORTY]["profile"] == PROFILE_B
    assert epochs[EPOCH_FIFTY]["profile"] == PROFILE_B


def test_revoked_lane_omits_epoch(roster_from_binary: dict):
    """Epoch with a required lane only-revoked must not publish."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_TWENTY_FIVE not in epochs
    assert set(epochs.keys()) == PUBLISHED_EPOCHS


def test_hold_keeps_epoch_with_reduced_accepted(roster_from_binary: dict):
    """Suspended co-presence keeps the epoch; accepted is only non-held trust."""
    epochs = _epoch_map(roster_from_binary)
    assert EPOCH_THIRTY in epochs
    assert epochs[EPOCH_THIRTY]["profile"] == PROFILE_A
    assert int(epochs[EPOCH_THIRTY]["accepted"]) >= BAND_LO
    assert int(epochs[EPOCH_THIRTY]["accepted"]) < BAND_CAP


def test_output_differs_from_surface(roster_from_binary: dict):
    """Deep attestation must disagree with the surface fixture on every shared epoch."""
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert roster_from_binary != surface
    surface_epochs = {int(e["id"]): e for e in surface[KEY_EPOCHS]}
    roster_epochs = _epoch_map(roster_from_binary)
    for eid in sorted(PUBLISHED_EPOCHS):
        assert eid in roster_epochs
        assert int(roster_epochs[eid]["accepted"]) < int(surface_epochs[eid]["accepted"])


def test_output_matches_rebuilt(roster_from_binary: dict):
    """On-disk agent output must match rebuilt trusteval."""
    assert OUTPUT.is_file(), f"missing {OUTPUT}"
    on_disk = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert on_disk == roster_from_binary


def test_attestation_stable_across_runs(roster_from_binary: dict):
    """Second attest run must match the first and stay below surface tallies."""
    second = _rebuild_and_attest(Path("/tmp") / "mesh-attestation-second.json")
    assert second == roster_from_binary
    epochs = _epoch_map(second)
    assert int(epochs[EPOCH_TEN]["accepted"]) < SURFACE_EPOCH_10
    assert EPOCH_THIRTY in epochs


def test_output_differs_from_surfskim(roster_from_binary: dict):
    """Agent output must differ from surfskim and beat surface inflation."""
    surface_poke = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert roster_from_binary != surface_poke
    assert OUTPUT.is_file()
    on_disk = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert on_disk == roster_from_binary
    assert on_disk != surface_poke
    assert Path("/app/bin").joinpath(SURFSKIM_BIN).is_file()
    epochs = _epoch_map(on_disk)
    poke_epochs = {int(e["id"]): e for e in surface_poke[KEY_EPOCHS]}
    assert int(epochs[EPOCH_TEN]["accepted"]) < int(poke_epochs[EPOCH_TEN]["accepted"])


def test_dynamic_frame_injection(roster_from_binary: dict):
    """Inject a valid frame and verify the evaluator incorporates it."""
    seg_path = SEGMENTS / "seg_99.bin"
    assert DYNAMIC_FRAME.is_file(), "dynamic test frame fixture missing"
    baseline = int(_epoch_map(roster_from_binary)[EPOCH_TEN]["accepted"])
    shutil.copy(DYNAMIC_FRAME, seg_path)
    try:
        roster = _rebuild_and_attest(DYNAMIC_OUT)
        epochs = _epoch_map(roster)
        assert int(epochs[EPOCH_TEN]["accepted"]) == baseline + 1, (
            f"Expected {baseline + 1} after injection, "
            f"got {epochs[EPOCH_TEN]['accepted']}"
        )
    finally:
        seg_path.unlink(missing_ok=True)


def test_dynamic_injected_frame_rejected(roster_from_binary: dict):
    """Inject a forged frame and verify it is rejected."""
    seg_path = SEGMENTS / "seg_98.bin"
    assert DYNAMIC_INJECTED.is_file(), "dynamic injected frame fixture missing"
    baseline = int(_epoch_map(roster_from_binary)[EPOCH_FORTY]["accepted"])
    shutil.copy(DYNAMIC_INJECTED, seg_path)
    try:
        roster = _rebuild_and_attest(DYNAMIC_OUT)
        epochs = _epoch_map(roster)
        assert int(epochs[EPOCH_FORTY]["accepted"]) == baseline, (
            f"Expected {baseline} (injected rejected), "
            f"got {epochs[EPOCH_FORTY]['accepted']}"
        )
    finally:
        seg_path.unlink(missing_ok=True)


def test_empty_authority_material_rejects_wal():
    """Empty authority seeds must not auto-accept WAL frames."""
    manifest = Path("/app/data/manifests/tier_intermediate.jsonl")
    backup = manifest.read_text(encoding="utf-8")
    out = Path("/tmp") / "mesh-attestation-empty-auth.json"
    try:
        blanked = []
        for line in backup.splitlines():
            if not line.strip():
                continue
            blanked.append(re.sub(r'"seed"\s*:\s*"[^"]*"', '"seed":""', line))
        manifest.write_text("\n".join(blanked) + "\n", encoding="utf-8")
        roster = _rebuild_and_attest(out)
        epochs = _epoch_map(roster)
        assert int(epochs[EPOCH_TEN]["accepted"]) < EPOCH_10_ACCEPTED
        reject = _load_reject_ledger(_reject_path_for(out))
        reasons = {e["reason"] for e in reject[KEY_REJECTED]}
        assert REASON_SEAL in reasons
    finally:
        manifest.write_text(backup, encoding="utf-8")


def test_all_zero_authority_material_rejects_wal():
    """All-zero derived authority material must not auto-accept WAL frames."""
    core = Path("/app/core/src/lib.rs")
    backup = core.read_text(encoding="utf-8")
    out = Path("/tmp") / "mesh-attestation-zero-auth.json"
    try:
        core.write_text(
            'pub const DATA_ROOT: &str = "/app/data";\n'
            'pub const OPS_ROOT: &str = "/app/ops";\n'
            'pub const CONFIG_ROOT: &str = "/app/config";\n'
            'pub const CREDENTIALS_DIR: &str = "/app/data/credentials";\n'
            'pub const SEGMENTS_DIR: &str = "/app/data/signed_segments";\n'
            "\n"
            "pub fn derive_epoch_key(seed: &[u8], _epoch: u16) -> Vec<u8> {\n"
            "    let n = if seed.is_empty() { 4 } else { seed.len() };\n"
            "    vec![0u8; n]\n"
            "}\n",
            encoding="utf-8",
        )
        roster = _rebuild_and_attest(out)
        epochs = _epoch_map(roster)
        assert int(epochs[EPOCH_TEN]["accepted"]) < EPOCH_10_ACCEPTED
        reject = _load_reject_ledger(_reject_path_for(out))
        assert len(_reason_keys(reject, REASON_SEAL)) >= MIN_SEAL_BREAKS
    finally:
        core.write_text(backup, encoding="utf-8")


def test_reject_ledger_structure(roster_from_binary: dict, reject_from_binary: dict):
    """Reject ledger lists rejected inputs with required reason vocabulary."""
    _ = roster_from_binary
    assert QUARANTINE.is_file(), f"missing {QUARANTINE}"
    data = _load_reject_ledger(QUARANTINE)
    rejected = data[KEY_REJECTED]
    assert len(rejected) >= MIN_REJECTED, (
        f"Expected at least {MIN_REJECTED} rejected frames, got {len(rejected)}"
    )
    reasons = {e["reason"] for e in rejected}
    assert REASON_SEAL in reasons
    assert REASON_REPLAY in reasons
    assert REASON_REVOKED in reasons
    for entry in rejected:
        assert "epoch" in entry
        assert "lane" in entry
        assert "ts" in entry
        assert entry["reason"] in QUARANTINE_REASONS
    assert _reason_keys(data, REASON_SEAL) == _reason_keys(reject_from_binary, REASON_SEAL)


def test_reject_ledger_seal_breaks(roster_from_binary: dict, reject_from_binary: dict):
    """Reject ledger contains seal_break entries for known forgeries."""
    _ = roster_from_binary
    data = _load_reject_ledger(QUARANTINE)
    seal_breaks = [e for e in data[KEY_REJECTED] if e["reason"] == REASON_SEAL]
    assert len(seal_breaks) >= MIN_SEAL_BREAKS
    failure_keys = _reason_keys(data, REASON_SEAL)
    assert failure_keys == _reason_keys(reject_from_binary, REASON_SEAL)
    assert (EPOCH_TEN, "lora", 850) in failure_keys
    assert (EPOCH_TEN, "mqtt", 920) in failure_keys
    assert (EPOCH_FORTY, "uart", 1350) in failure_keys


def test_reject_ledger_replay_entries(roster_from_binary: dict, reject_from_binary: dict):
    """Reject ledger contains core replay entries for non-advancing streams."""
    _ = roster_from_binary
    data = _load_reject_ledger(QUARANTINE)
    replays = [e for e in data[KEY_REJECTED] if e["reason"] == REASON_REPLAY]
    assert len(replays) >= MIN_REPLAYS
    replay_keys = _reason_keys(data, REASON_REPLAY)
    assert replay_keys == _reason_keys(reject_from_binary, REASON_REPLAY)
    assert replay_keys == EXPECTED_REPLAY_KEYS


def test_reject_ledger_revoked_entries(roster_from_binary: dict, reject_from_binary: dict):
    """Reject ledger contains revoked WAL frames."""
    _ = roster_from_binary
    data = _load_reject_ledger(QUARANTINE)
    revoked = [e for e in data[KEY_REJECTED] if e["reason"] == REASON_REVOKED]
    assert len(revoked) >= MIN_REVOKED
    revoked_keys = _reason_keys(data, REASON_REVOKED)
    assert revoked_keys == _reason_keys(reject_from_binary, REASON_REVOKED)
    assert (EPOCH_TWENTY, "lora", 1600) in revoked_keys
    assert (EPOCH_TWENTY_FIVE, "lora", 950) in revoked_keys


def test_fixtures_untouched():
    """Seed and surface fixtures remain as shipped."""
    data = json.loads(SEED.read_text(encoding="utf-8"))
    assert data.get("seed") == SEED_NAME
    assert data.get("preserve") is True
    surface = json.loads(SURFACE.read_text(encoding="utf-8"))
    assert surface.get("version") == SCHEMA_VERSION
    assert int(surface[KEY_EPOCHS][0]["accepted"]) == SURFACE_EPOCH_10
    audit = (FIXTURES / "pre_incident_audit.log").read_text(encoding="utf-8")
    assert SAMPLE_A in audit
    assert SAMPLE_B in audit
    assert len(re.findall(r"material_hex=[0-9a-f]{8}", audit)) >= 2
    assert len(re.findall(r"seed_hex=[0-9a-f]{8}", audit)) >= 2
    assert len(re.findall(r"check=0x[0-9a-f]{2}", audit)) >= 2
