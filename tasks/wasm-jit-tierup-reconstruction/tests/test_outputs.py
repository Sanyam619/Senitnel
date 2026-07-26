"""Verifier tests for multi-authority WASM tier-up admission."""

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/warmup-report.json")

ALLOWED = {
    "benign_type_stable",
    "benign_table_stable",
    "benign_epoch_bumped",
    "held_polymorphic",
    "interpreter_only",
    "type_bypass_blocked",
    "arity_bypass_blocked",
    "bounds_bypass_blocked",
    "table_bypass_blocked",
}

EXPECTED = {
    "b1": ("promoted", True, "benign_type_stable", []),
    "b2": ("promoted", False, "benign_table_stable", []),
    "b3": ("held", False, "held_polymorphic", ["type"]),
    "b4": ("promoted", True, "benign_epoch_bumped", ["arity", "bounds", "table", "type"]),
    "b5": ("refused", False, "interpreter_only", []),
    "b6": ("promoted", True, "benign_epoch_bumped", ["arity", "bounds", "table", "type"]),
    "x1": ("held", False, "type_bypass_blocked", ["arity", "bounds", "table", "type"]),
    "x2": ("held", False, "arity_bypass_blocked", ["arity", "bounds", "table", "type"]),
    "x3": ("held", False, "bounds_bypass_blocked", ["arity", "bounds", "table", "type"]),
    "x4": ("held", False, "table_bypass_blocked", ["arity", "bounds", "table", "type"]),
}

REQUIRED_PATHS = [
    Path("/app/data/scenarios"),
    Path("/app/data/authority"),
    Path("/app/data/authority/profile"),
    Path("/app/data/authority/rebind"),
    Path("/app/data/authority/floor"),
    Path("/app/data/manifest/registry.sig"),
    Path("/app/bin/fastcheck"),
    Path("/app/bin/warmup"),
    Path("/app/docs/report-schema.md"),
    Path("/app/docs/authority-notes.md"),
    Path("/app/data/coredump/partial.json"),
]


def _run():
    subprocess.run(["/app/scripts/run-engine.sh"], check=True)


def _load():
    assert REPORT.is_file()
    return json.loads(REPORT.read_text())


def _by_id(data):
    return {r["id"]: r for r in data["scenarios"]}


def _assert_row(sid: str):
    _run()
    row = _by_id(_load())[sid]
    exp = EXPECTED[sid]
    assert (row["outcome"], row["host_call_permitted"], row["category"]) == exp[:3]
    assert sorted(row["checks_installed"]) == exp[3]


class TestOutputs:
    def test_schema_and_epoch_contract(self):
        """Schema keys, schema version, closed categories, and registry epoch."""
        _run()
        data = _load()
        assert set(data.keys()) == {"schema_version", "registry_epoch", "scenarios"}
        assert data["schema_version"] == "warmup-report-1"
        assert data["registry_epoch"] == 1
        for row in data["scenarios"]:
            assert set(row.keys()) == {
                "id", "outcome", "host_call_permitted", "category", "checks_installed"
            }
            assert row["outcome"] in {"promoted", "held", "refused"}
            assert row["category"] in ALLOWED
            if row["category"] == "benign_epoch_bumped":
                assert sorted(row["checks_installed"]) == [
                    "arity", "bounds", "table", "type"
                ]

    def test_all_scenarios_present(self):
        """Report covers the full embedded scenario id set exactly once."""
        _run()
        got = sorted(r["id"] for r in _load()["scenarios"])
        assert got == sorted(EXPECTED.keys())
        assert len(got) == len(set(got))

    def test_scenarios_sorted_by_id(self):
        """Scenario rows must be emitted in ascending id order."""
        _run()
        ids = [r["id"] for r in _load()["scenarios"]]
        assert ids == sorted(ids)
        assert ids == sorted(EXPECTED.keys())

    def test_required_fixtures_preserved(self):
        """Protected fixtures and rebuilt host binary remain in place."""
        _run()
        for path in REQUIRED_PATHS:
            assert path.exists(), f"missing required path: {path}"
        for sid in EXPECTED:
            assert (Path("/app/data/scenarios") / f"{sid}.case").is_file()
            assert (Path("/app/data/authority/profile") / f"{sid}.prof").is_file()
            assert (Path("/app/data/authority/rebind") / f"{sid}.rbnd").is_file()
            assert (Path("/app/data/authority/floor") / f"{sid}.flr").is_file()
        assert Path("/app/bin/warmup").is_file()
        assert Path("/app/bin/warmup").stat().st_size > 0
        sig = Path("/app/data/manifest/registry.sig").read_text()
        assert "epoch=" in sig

    def test_surface_ok_does_not_imply_isolation(self):
        """Exploit rows must stay held off-host even when a soft probe would pass."""
        _run()
        by_id = _by_id(_load())
        for sid in ("x1", "x2", "x3", "x4"):
            assert by_id[sid]["outcome"] == "held"
            assert by_id[sid]["host_call_permitted"] is False

    def test_b1_type_stable_promotion(self):
        """Stable monomorphic site with a legit host call promotes cleanly."""
        _assert_row("b1")

    def test_b2_table_stable_promotion(self):
        """Stable indirect-call site without host attempt promotes."""
        _assert_row("b2")

    def test_b3_polymorphic_hold_ignores_floor_bait(self):
        """Polymorphic profile must hold even when floor bait says promote."""
        _assert_row("b3")

    def test_b4_reload_without_signature_delta(self):
        """Reload with unchanged signature promotes under refresh guards."""
        _assert_row("b4")

    def test_b5_cold_refused(self):
        """Cold site is refused as interpreter-only."""
        _assert_row("b5")

    def test_b6_probe_batch_crossed_reload(self):
        """Probe batch that straddled a reload keeps refresh guards."""
        _assert_row("b6")

    def test_x1_type_rebinding_blocked(self):
        """Type rebinding is held with the full guard set."""
        _assert_row("x1")

    def test_x2_arity_rebinding_blocked(self):
        """Arity rebinding is held with the full guard set."""
        _assert_row("x2")

    def test_x3_bounds_rebinding_blocked(self):
        """Bounds rebinding is held with the full guard set."""
        _assert_row("x3")

    def test_x4_table_rebinding_blocked(self):
        """Table rebinding is held with the full guard set."""
        _assert_row("x4")

    def test_no_exploit_reaches_host(self):
        """Exploit variants stay mid-tier held with host crossings denied."""
        _run()
        by_id = _by_id(_load())
        for sid in ("x1", "x2", "x3", "x4"):
            row = by_id[sid]
            assert row["host_call_permitted"] is False
            assert row["outcome"] == "held"
            assert sorted(row["checks_installed"]) == ["arity", "bounds", "table", "type"]

    def test_floor_bait_does_not_control_matrix(self):
        """Floor promote hints must not override polymorphic, exploit, or cold paths."""
        _run()
        by_id = _by_id(_load())
        assert by_id["b3"]["category"] == "held_polymorphic"
        assert by_id["x1"]["category"] == "type_bypass_blocked"
        assert by_id["b5"]["category"] == "interpreter_only"

    def test_benign_matrix_matches_contract(self):
        """Benign scenario matrix matches the report contract outcomes."""
        _run()
        by_id = _by_id(_load())
        for sid in ("b1", "b2", "b3", "b4", "b5", "b6"):
            exp = EXPECTED[sid]
            row = by_id[sid]
            assert row["outcome"] == exp[0]
            assert row["host_call_permitted"] == exp[1]
            assert row["category"] == exp[2]
            assert sorted(row["checks_installed"]) == exp[3]

    def test_idempotent_across_reruns(self):
        """Two consecutive engine runs produce identical reports."""
        _run()
        first = _load()
        _run()
        second = _load()
        assert first == second
        by_id = _by_id(first)
        assert by_id["b4"]["category"] == "benign_epoch_bumped"
        assert sorted(by_id["b4"]["checks_installed"]) == [
            "arity", "bounds", "table", "type"
        ]
        assert by_id["b6"]["category"] == "benign_epoch_bumped"
        assert sorted(by_id["b6"]["checks_installed"]) == [
            "arity", "bounds", "table", "type"
        ]

    def test_report_categories_are_closed_set(self):
        """Every emitted category is one of the documented closed tokens."""
        _run()
        for row in _load()["scenarios"]:
            assert row["category"] in ALLOWED
