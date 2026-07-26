"""Verifier tests for edge admission ledger outcomes."""

import json
import subprocess
from pathlib import Path

LEDGER = Path("/output/admit-ledger.json")
RUNTIME = Path("/app/data/state/runtime.json")
RESTORE_TRUST = Path("/app/data/restore/trust.bundle")
RESTORE_PINS = Path("/app/data/restore/pins.hot")

EXPECTED_EPOCH = 21
# checksum of the live runtime fixture the reload path must preserve
RUNTIME_BODY = '{"epoch": 21, "lane": "edge-a"}\n'
TRUST_BODY = "gen=17\nroot=restore-root-17\nlineage=lin-17\n"
PINS_BODY = "lineage=lin-17\npin=hot-17\n"

EXPECTED = {
    "k9": ("reject", "revoked"),
    "m2": ("accept", "ok_aligned"),
    "n4": ("reject", "stale_cache"),
    "p7": ("reject", "lineage_skew"),
    "q3": ("reject", "gen_skew"),
    "t1": ("reject", "lineage_skew"),
    "w2": ("reject", "conflict"),
}


def runtime_epoch() -> int:
    raw = RUNTIME.read_text()
    assert raw == RUNTIME_BODY
    return int(json.loads(raw)["epoch"])


def load_ledger():
    assert LEDGER.is_file(), "admit ledger missing"
    return json.loads(LEDGER.read_text())


def by_id(data):
    return {row["id"]: row for row in data["cases"]}


def run_admit():
    subprocess.run(["/app/scripts/run-admit.sh"], check=True)


def run_reload():
    subprocess.run(["/app/scripts/edge-reload.sh"], check=True)


def restore_restore_fixtures() -> None:
    RESTORE_TRUST.write_text(TRUST_BODY)
    RESTORE_PINS.write_text(PINS_BODY)
    RUNTIME.write_text(RUNTIME_BODY)


class TestOutputs:
    def test_emit_json_contract(self):
        """Ledger schema, schema_version, and reload_epoch match runtime."""
        run_admit()
        data = load_ledger()
        assert set(data.keys()) == {"schema_version", "cases", "reload_epoch"}
        assert data["schema_version"] == "edge-admit-1"
        assert data["reload_epoch"] == EXPECTED_EPOCH
        assert runtime_epoch() == EXPECTED_EPOCH
        ids = {row["id"] for row in data["cases"]}
        assert ids == set(EXPECTED.keys())
        for row in data["cases"]:
            assert set(row.keys()) == {"id", "decision", "reason_code"}
            assert row["decision"] in {"accept", "reject"}

    def test_k9_slot_deny(self):
        """Revoked capability material must be refused."""
        run_admit()
        row = by_id(load_ledger())["k9"]
        assert row["decision"] == EXPECTED["k9"][0]
        assert row["reason_code"] == EXPECTED["k9"][1]

    def test_m2_slot_allow(self):
        """Fully aligned peer must be admitted."""
        run_admit()
        row = by_id(load_ledger())["m2"]
        assert row["decision"] == EXPECTED["m2"][0]
        assert row["reason_code"] == EXPECTED["m2"][1]

    def test_n4_stale_window(self):
        """Fresh revocation must win over cached allow on refresh."""
        run_admit()
        row = by_id(load_ledger())["n4"]
        assert row["decision"] == EXPECTED["n4"][0]
        assert row["reason_code"] == EXPECTED["n4"][1]

    def test_p7_skew_hot(self):
        """Claim lineage mismatch against active material must be refused."""
        run_admit()
        row = by_id(load_ledger())["p7"]
        assert row["decision"] == EXPECTED["p7"][0]
        assert row["reason_code"] == EXPECTED["p7"][1]

    def test_q3_gen_skew(self):
        """Restore-generation store claim must be refused under current runtime."""
        run_admit()
        row = by_id(load_ledger())["q3"]
        assert row["decision"] == EXPECTED["q3"][0]
        assert row["reason_code"] == EXPECTED["q3"][1]

    def test_r8_hold_same(self):
        """Decisions, reload_epoch, and runtime epoch stay stable across reload."""
        try:
            run_admit()
            first = load_ledger()
            first_map = {
                row["id"]: (row["decision"], row["reason_code"]) for row in first["cases"]
            }
            assert set(first_map) == set(EXPECTED)
            assert first["reload_epoch"] == EXPECTED_EPOCH
            assert runtime_epoch() == EXPECTED_EPOCH
            run_reload()
            assert runtime_epoch() == EXPECTED_EPOCH
            run_admit()
            second = load_ledger()
            second_map = {
                row["id"]: (row["decision"], row["reason_code"]) for row in second["cases"]
            }
            assert second["reload_epoch"] == EXPECTED_EPOCH
            assert first_map == second_map
        finally:
            restore_restore_fixtures()

    def test_t1_rank_mix(self):
        """Subject aligned only to restore hot lineage must be refused."""
        run_admit()
        row = by_id(load_ledger())["t1"]
        assert row["decision"] == EXPECTED["t1"][0]
        assert row["reason_code"] == EXPECTED["t1"][1]

    def test_w2_dual_fail(self):
        """Combined generation and lineage failure must surface as conflict."""
        run_admit()
        row = by_id(load_ledger())["w2"]
        assert row["decision"] == EXPECTED["w2"][0]
        assert row["reason_code"] == EXPECTED["w2"][1]
