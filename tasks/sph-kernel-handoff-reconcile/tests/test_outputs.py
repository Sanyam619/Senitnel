"""Hard scoring tests for the SPH handoff reconciliation task.

The session-scoped fixture in ``conftest.py`` rebuilds ``/app/ws`` from
live sources and emits ``/output/reconcile-report.json`` before any
test here inspects it, and it also builds the verifier-owned
``/logs/verifier/sph-verify`` binary that exercises the internal crates with
verifier-controlled inputs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def _finite(v: float) -> bool:
    # Rejects NaN (± comparisons are false) and ±inf without self-compare
    # (ruff PLR0124) or importing math (collapse GX8 on stdlib-as-domain).
    return float("-inf") < v < float("inf")


REPORT_PATH = Path("/output/reconcile-report.json")
CHECKPOINTS_DIR = Path("/app/data/checkpoints")
POLICY_PATH = Path("/app/data/policy/handoff.spec")
POLICY_CANON_PATH = Path("/app/data/policy/handoff.canon")
HANDOFF_ACCEPT_PATH = Path("/app/data/state/root.accept")
TRIAL_PREF_PATH = Path("/app/data/state/trial_pref.toml")
SPH_VERIFY_BIN = Path("/logs/verifier/sph-verify")

SCENARIOS = ("sod_shock_tube", "sedov_blast", "kelvin_helmholtz", "poly_star")
KERNEL_LABELS = ("cubic_spline", "wendland_c4")
RESIDUAL_KEYS = (
    "moment_zero_residual",
    "h_consistency_residual",
    "momentum_residual",
    "angular_residual",
    "gravity_virial_residual",
    "chunk_stability_delta",
)
INVARIANT_KEYS = (
    "max_moment_zero",
    "max_h_consistency",
    "max_momentum",
    "max_angular",
)


def _load_report() -> dict:
    assert REPORT_PATH.exists(), f"missing {REPORT_PATH}"
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def _index_rows(report: dict) -> dict[str, dict]:
    return {row["scenario"]: row for row in report["scenarios"]}


def _read_spec(name: str) -> dict:
    path = CHECKPOINTS_DIR / f"{name}.spec"
    assert path.exists(), f"missing checkpoint spec {path}"
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"')
    return out


def _read_policy() -> dict:
    out: dict[str, str] = {}
    assert POLICY_PATH.exists(), f"missing {POLICY_PATH}"
    for raw in POLICY_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"')
    return out


def _read_policy_canon() -> dict:
    out: dict[str, str] = {}
    assert POLICY_CANON_PATH.exists(), f"missing {POLICY_CANON_PATH}"
    for raw in POLICY_CANON_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"')
    return out


BANDS: dict[str, dict[str, float]] = {
    "sod_shock_tube": {
        "band_moment_zero": 0.6,
        "band_h_consistency": 1e-2,
        "band_momentum": 1e-6,
        "band_angular": 1e-6,
        "band_chunk_stability": 1e-12,
    },
    "sedov_blast": {
        "band_moment_zero": 0.6,
        "band_h_consistency": 1e-2,
        "band_momentum": 1e-6,
        "band_angular": 1e-6,
        "band_chunk_stability": 1e-12,
    },
    "kelvin_helmholtz": {
        "band_moment_zero": 0.6,
        "band_h_consistency": 1e-2,
        "band_momentum": 1e-6,
        "band_angular": 1e-6,
        "band_chunk_stability": 1e-12,
    },
    "poly_star": {
        "band_moment_zero": 0.6,
        "band_h_consistency": 1e-2,
        "band_momentum": 1e-6,
        "band_angular": 1e-6,
        "band_gravity_virial": 5e-2,
        "band_chunk_stability": 1e-12,
    },
}


def _band(name: str, key: str) -> float:
    return BANDS[name][key]


def test_report_schema_and_tag():
    """Report is a JSON object with the fixed schema_tag and top-level keys."""
    report = _load_report()
    assert isinstance(report, dict)
    assert set(report.keys()) == {"schema_tag", "scenarios", "invariants"}
    assert report["schema_tag"] == "sph-reconcile-v1"


def test_all_scenarios_present_exactly():
    """Exactly the four bundled checkpoints must appear, no more, no less."""
    rows = _index_rows(_load_report())
    assert set(rows.keys()) == set(SCENARIOS), rows.keys()


def test_row_schema_and_types():
    """Each row exposes the documented columns with correct types."""
    expected = {
        "scenario",
        "kernel_source",
        "kernel_target",
        "particles",
        "converged",
        *RESIDUAL_KEYS,
    }
    for row in _load_report()["scenarios"]:
        assert set(row.keys()) == expected, row.keys()
        assert isinstance(row["scenario"], str)
        assert isinstance(row["kernel_source"], str)
        assert isinstance(row["kernel_target"], str)
        assert isinstance(row["particles"], int) and row["particles"] > 0
        assert isinstance(row["converged"], bool)
        for k in RESIDUAL_KEYS:
            v = row[k]
            assert isinstance(v, (int, float)) and not isinstance(v, bool), k
            assert _finite(float(v)), f"{row['scenario']}.{k} not finite: {v}"
            assert float(v) >= 0.0, f"{row['scenario']}.{k} negative: {v}"


def test_invariants_keys_and_types():
    """The invariants block carries the four aggregate maxima."""
    inv = _load_report()["invariants"]
    assert set(inv.keys()) == set(INVARIANT_KEYS), inv.keys()
    for k in INVARIANT_KEYS:
        v = inv[k]
        assert isinstance(v, (int, float)) and not isinstance(v, bool)
        assert _finite(float(v)) and float(v) >= 0.0


def test_kernel_labels_and_particle_counts():
    """Kernel labels are known and particles match each checkpoint spec."""
    rows = _index_rows(_load_report())
    for name in SCENARIOS:
        row = rows[name]
        spec = _read_spec(name)
        assert row["kernel_source"] in KERNEL_LABELS
        assert row["kernel_target"] in KERNEL_LABELS
        assert row["particles"] == int(spec["n_particles"])
        assert row["kernel_source"] == spec["source_kernel"]


def test_policy_kernel_authority():
    """Report and durable handoff follow the canonical policy authority."""
    canon = _read_policy_canon()
    selected = canon["selected_kernel"]
    policy = _read_policy()
    assert policy["selected_kernel"] == selected
    assert policy.get("authority") == canon.get("authority")
    rows = _index_rows(_load_report())
    for name in SCENARIOS:
        spec = _read_spec(name)
        assert spec["source_kernel"] != selected, name
        assert rows[name]["kernel_target"] == selected, rows[name]
        assert rows[name]["kernel_source"] == spec["source_kernel"]


def test_residuals_reflect_real_numeric_work():
    """h_consistency and moment_zero must reflect live measured residuals."""
    rows = _load_report()["scenarios"]
    h_total = sum(float(r["h_consistency_residual"]) for r in rows)
    mz_vals = [float(r["moment_zero_residual"]) for r in rows]
    assert h_total > 0.0
    assert any(v > 1e-6 for v in mz_vals), mz_vals
    for row in rows:
        assert _finite(float(row["moment_zero_residual"]))


def test_durable_material_preference():
    """Durable root.accept must own density/force materials; live trial pref gone."""
    assert HANDOFF_ACCEPT_PATH.is_file(), "missing /app/data/state/root.accept"
    assert not TRIAL_PREF_PATH.exists(), "live trial_pref.toml must not remain"
    text = HANDOFF_ACCEPT_PATH.read_text(encoding="utf-8")
    roots = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        roots[k.strip()] = v.strip().strip('"')
    assert roots.get("material_root") == "durable", roots


def test_durable_material_preference_survives_rebuild():
    """Rebuilding under the durable accept must keep Shepard density materials."""
    assert HANDOFF_ACCEPT_PATH.is_file()
    assert not TRIAL_PREF_PATH.exists()
    HANDOFF_ACCEPT_PATH.write_text("material_root = durable\n", encoding="utf-8")
    env = os.environ.copy()
    env["PATH"] = "/usr/local/cargo/bin:" + env.get("PATH", "")
    cargo = shutil.which("cargo", path=env["PATH"]) or "/usr/local/cargo/bin/cargo"
    build = subprocess.run(
        [
            cargo,
            "build",
            "-p",
            "sph_a",
            "-p",
            "sph_b",
            "-p",
            "sph_verify",
            "--release",
            "--locked",
            "--offline",
        ],
        cwd="/app/ws",
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (build.stdout[-1500:] + build.stderr[-1500:])
    bin_src = Path("/app/ws/target/release/sph-verify")
    assert bin_src.is_file()
    shutil.copyfile(bin_src, SPH_VERIFY_BIN)
    res = subprocess.run(
        [str(SPH_VERIFY_BIN), "normalization"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr



def test_all_scenarios_converged():
    """Every scenario must reach the smoothing-length tolerance."""
    for row in _load_report()["scenarios"]:
        assert row["converged"] is True, row["scenario"]


@pytest.mark.parametrize("name", SCENARIOS)
def test_moment_zero_within_band(name):
    """Per-scenario zeroth-moment residual must sit inside the band."""
    row = _index_rows(_load_report())[name]
    band = _band(name, "band_moment_zero")
    assert row["moment_zero_residual"] <= band, (row, band)


@pytest.mark.parametrize("name", SCENARIOS)
def test_h_consistency_within_band(name):
    """Per-scenario smoothing-length constraint residual must sit inside the band."""
    row = _index_rows(_load_report())[name]
    band = _band(name, "band_h_consistency")
    assert row["h_consistency_residual"] <= band, (row, band)


@pytest.mark.parametrize("name", SCENARIOS)
def test_momentum_within_band(name):
    """Per-scenario momentum residual must sit inside the band."""
    row = _index_rows(_load_report())[name]
    band = _band(name, "band_momentum")
    assert row["momentum_residual"] <= band, (row, band)


@pytest.mark.parametrize("name", SCENARIOS)
def test_angular_within_band(name):
    """Per-scenario angular momentum residual must sit inside the band."""
    row = _index_rows(_load_report())[name]
    band = _band(name, "band_angular")
    assert row["angular_residual"] <= band, (row, band)


@pytest.mark.parametrize("name", SCENARIOS)
def test_chunk_stability_within_band(name):
    """Chunked reduction must be invariant across probed chunk sizes."""
    row = _index_rows(_load_report())[name]
    band = _band(name, "band_chunk_stability")
    assert row["chunk_stability_delta"] <= band, (row, band)


def test_gravity_virial_only_for_gravitating_scenario():
    """Only the self-gravitating scenario carries a virial band."""
    rows = _index_rows(_load_report())
    for name in SCENARIOS:
        spec = _read_spec(name)
        is_gravitating = spec.get("self_gravitating", "false").lower() == "true"
        v = rows[name]["gravity_virial_residual"]
        if is_gravitating:
            band = _band(name, "band_gravity_virial")
            assert v <= band, (name, v, band)
        else:
            assert v == 0.0, (name, v)


def test_invariants_recomputed_from_scenarios():
    """The invariants block must equal the recomputed max across scenarios."""
    report = _load_report()
    inv = report["invariants"]
    rows = report["scenarios"]
    mapping = {
        "max_moment_zero": "moment_zero_residual",
        "max_momentum": "momentum_residual",
        "max_angular": "angular_residual",
        "max_h_consistency": "h_consistency_residual",
    }
    for agg, per_row in mapping.items():
        expected = max(float(r[per_row]) for r in rows)
        got = float(inv[agg])
        assert got == expected, (agg, got, expected)


def test_density_not_trivially_equal_to_raw_sph():
    """Shepard-published density must differ from raw rho_hat on these layouts.

    ``moment_zero_residual`` is peak relative |rho_shepard − rho_hat| / scale.
    Identity (raw-only) publication leaves every scenario at 0; at least one
    scenario must show a real Shepard shift.
    """
    residuals = [
        float(row["moment_zero_residual"]) for row in _load_report()["scenarios"]
    ]
    assert any(r > 1e-6 for r in residuals), residuals


class TestSubsystemProbes:
    """Drive the verifier-owned sph-verify binary against live crates."""

    def _run(self, subcommand: str) -> subprocess.CompletedProcess:
        assert SPH_VERIFY_BIN.exists(), f"missing verifier binary {SPH_VERIFY_BIN}"
        return subprocess.run(
            [str(SPH_VERIFY_BIN), subcommand],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_probe_density_field(self):
        """Published densities must match the verifier's reference reconstruction."""
        res = self._run("normalization")
        assert res.returncode == 0, res.stderr

    def test_probe_smoothing_length_pass(self):
        """The smoothing-length pass must reach tolerance under a corrupted start."""
        res = self._run("hiterate")
        assert res.returncode == 0, res.stderr

    def test_probe_pairwise_forces(self):
        """Pairwise pressure kicks must conserve linear and angular momentum."""
        res = self._run("symmetry")
        assert res.returncode == 0, res.stderr

    def test_probe_greens_coefficient(self):
        """Self-gravity coefficient must follow the active kernel handle."""
        res = self._run("greens")
        assert res.returncode == 0, res.stderr

    def test_probe_chunked_reduction(self):
        """Reduction of a cancellation stream must not depend on chunk size."""
        res = self._run("chunkreduce")
        assert res.returncode == 0, res.stderr
