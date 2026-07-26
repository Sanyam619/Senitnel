"""Hard macroscopic-invariant checks for the LBM campaign report.

Also drives the verifier-owned ``lbmverify`` binary (staged and built by
``conftest.py``) so that configuration selection, snapshot round trips
including halo handling, and interior-only worker-independent reductions
are checked against the current internal packages with verifier-controlled
inputs. This makes fabricated ``/output/campaign-report.json`` files or
doctored campaign drivers unable to hide defects the agent must repair.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPORT = Path("/output/campaign-report.json")
SCHEMA_DOC = Path("/app/docs/report-schema.md")
GRID_ROOT = Path("/app/data/cases")
MANIFEST_ROOT = Path("/app/config/manifests")
LBMVERIFY_BIN = Path("/app/bin/lbmverify")

LABELS = ("cavity", "couette", "poiseuille")
WORKERS = (1, 2, 4)
MODES = ("cold", "resume")
ROW_KEYS = {
    "label",
    "workers",
    "mode",
    "mean_rho",
    "mom_x",
    "mom_y",
    "ke",
    "mass",
    "stable",
}

# Bands from report-schema.md / physical closure expectations.
PAIR_BAND = 1e-3
SPAN_BAND = 1e-3
MASS_BAND = 1e-2
# Manifest omega=1.0 cavity attractor floor (above build-meta omega path).
# Documented in /app/docs/report-schema.md under "Configuration authority"
# and "Physical bounds enforced by the verifier", and surfaced in the task
# instruction. Any change here must be reflected in both places (test_band_mx
# enforces the doc contract).
CAVITY_MOM_FLOOR = 7.0e-3


def rel_gap(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def rel_spread(vals: list[float]) -> float:
    lo, hi = min(vals), max(vals)
    return (hi - lo) / max(abs(lo), abs(hi), 1e-12)


def load_report() -> dict:
    assert REPORT.is_file(), "campaign report missing"
    return json.loads(REPORT.read_text())


def rows_by() -> dict[tuple[str, int, str], dict]:
    data = load_report()
    out = {}
    for row in data["cases"]:
        out[(row["label"], int(row["workers"]), row["mode"])] = row
    return out


def rho0_for(label: str) -> tuple[float, int, int]:
    grid = json.loads((GRID_ROOT / label / "grid.json").read_text())
    return float(grid["rho0"]), int(grid["nx"]), int(grid["ny"])


class TestOutputs:
    def test_schema_surface(self):
        """Report exists with schema_tag, cases, parity, and exact row keys."""
        data = load_report()
        assert data["schema_tag"] == "lbm-campaign-v1"
        assert set(data.keys()) == {"schema_tag", "cases", "parity"}
        assert set(data["parity"].keys()) == {
            "cold_resume_max_rel",
            "worker_spread_max_rel",
        }
        assert len(data["cases"]) >= len(LABELS) * len(WORKERS) * len(MODES)
        for row in data["cases"]:
            assert set(row.keys()) == ROW_KEYS

    def test_label_matrix(self):
        """Every case label appears for workers 1/2/4 under cold and resume."""
        idx = rows_by()
        for label in LABELS:
            for w in WORKERS:
                for mode in MODES:
                    assert (label, w, mode) in idx

    def test_finite_rows(self):
        """Every row is marked stable with finite macroscopic fields."""
        for row in load_report()["cases"]:
            assert row["stable"] is True
            for key in ("mean_rho", "mom_x", "mom_y", "ke", "mass"):
                val = float(row[key])
                # Finite: not NaN and not ±inf, using only built-ins.
                assert val == val, f"{row['label']} {key} not finite"
                assert val not in (float("inf"), float("-inf")), (
                    f"{row['label']} {key} not finite"
                )

    def test_pair_gap_mx(self):
        """Cold vs resume mom_x relative gap stays within the schema band."""
        idx = rows_by()
        for label in LABELS:
            for w in WORKERS:
                cold = idx[(label, w, "cold")]
                resume = idx[(label, w, "resume")]
                assert rel_gap(cold["mom_x"], resume["mom_x"]) <= PAIR_BAND

    def test_pair_gap_ke(self):
        """Cold vs resume kinetic energy relative gap stays within the schema band."""
        idx = rows_by()
        for label in LABELS:
            for w in WORKERS:
                cold = idx[(label, w, "cold")]
                resume = idx[(label, w, "resume")]
                assert rel_gap(cold["ke"], resume["ke"]) <= PAIR_BAND

    def test_span_rho(self):
        """mean_rho does not drift across worker counts for cold runs."""
        idx = rows_by()
        for label in LABELS:
            vals = [idx[(label, w, "cold")]["mean_rho"] for w in WORKERS]
            assert rel_spread(vals) <= SPAN_BAND

    def test_span_integral(self):
        """mass does not drift across worker counts for cold runs."""
        idx = rows_by()
        for label in LABELS:
            vals = [idx[(label, w, "cold")]["mass"] for w in WORKERS]
            assert rel_spread(vals) <= SPAN_BAND

    def test_integral_closed(self):
        """mass stays within the documented closure band of nx*ny*rho0."""
        for row in load_report()["cases"]:
            rho0, nx, ny = rho0_for(row["label"])
            target = rho0 * nx * ny
            err = abs(row["mass"] - target) / target
            assert err <= MASS_BAND, f"{row['label']} w={row['workers']} mass err {err}"

    def test_gap_block(self):
        """parity fields match recomputed cold/resume and worker spreads."""
        data = load_report()
        idx = rows_by()
        cold_resume = 0.0
        for label in LABELS:
            for w in WORKERS:
                c = idx[(label, w, "cold")]
                r = idx[(label, w, "resume")]
                for key in ("mean_rho", "mom_x", "mom_y", "ke", "mass"):
                    cold_resume = max(cold_resume, rel_gap(c[key], r[key]))
        worker_spread = 0.0
        for label in LABELS:
            for key in ("mean_rho", "mom_x", "mom_y", "ke", "mass"):
                vals = [idx[(label, w, "cold")][key] for w in WORKERS]
                worker_spread = max(worker_spread, rel_spread(vals))
        assert abs(data["parity"]["cold_resume_max_rel"] - cold_resume) < 1e-9
        assert abs(data["parity"]["worker_spread_max_rel"] - worker_spread) < 1e-9
        assert data["parity"]["cold_resume_max_rel"] <= PAIR_BAND
        assert data["parity"]["worker_spread_max_rel"] <= SPAN_BAND

    def test_band_mx(self):
        """Cavity cold mom_x must sit on the manifest-governed attractor, not build-meta.

        The floor is a physical bound documented in /app/docs/report-schema.md
        (see 'Physical bounds enforced by the verifier') and referenced from
        the task instruction, so agents cannot be surprised by an undocumented
        threshold. This test also asserts the doc still carries the contract.
        """
        idx = rows_by()
        for w in WORKERS:
            row = idx[("cavity", w, "cold")]
            assert abs(row["mom_x"]) >= CAVITY_MOM_FLOOR, (
                f"cavity cold w={w} |mom_x|={abs(row['mom_x']):.3e} < floor "
                f"{CAVITY_MOM_FLOOR:.3e}; likely running under build-meta "
                "omega instead of the manifest value"
            )
        text = SCHEMA_DOC.read_text()
        assert "cold_resume_max_rel" in text
        assert "1e-3" in text
        # Manifest-governed cavity attractor floor must be documented.
        assert "cavity_mom_x_floor" in text, (
            "report-schema.md must document the cavity_mom_x_floor bound"
        )
        assert "7e-3" in text, (
            "report-schema.md must document the numeric cavity |mom_x| floor "
            "(7e-3) so agents see the physical bound"
        )
        # Manifest authority principle must be documented in the same file
        # so agents know which config source governs when they disagree.
        assert "Configuration authority" in text, (
            "report-schema.md must document the manifest-vs-build authority "
            "rule under a 'Configuration authority' heading"
        )
        assert MANIFEST_ROOT.joinpath("cavity.toml").is_file()


def _run_lbmverify(name: str) -> None:
    """Invoke the verifier-owned Go binary with the given subcommand."""
    assert LBMVERIFY_BIN.is_file() and os.access(LBMVERIFY_BIN, os.X_OK), (
        f"lbmverify binary missing at {LBMVERIFY_BIN}; conftest.py should have "
        "built it against the current /app sources"
    )
    result = subprocess.run(
        [os.fspath(LBMVERIFY_BIN), name],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"lbmverify {name} failed with exit {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            pytrace=False,
        )


class TestSubsystems:
    """Behavioral checks that exercise the internal packages directly.

    These tests invoke the verifier-owned lbmverify binary built by
    conftest.py. The binary imports the current internal packages under
    /app and drives them with inputs the verifier picks, so a hand-written
    /output/campaign-report.json or a substituted run_campaign.sh cannot
    satisfy them without the underlying packages actually being correct.
    """

    def test_authority_selection(self):
        """Resolver must honor the manifest-derived blob."""
        _run_lbmverify("policy")

    def test_checkpoint_round_trip(self):
        """Encode/Unpack must round-trip interior and X-halo cells."""
        _run_lbmverify("snap")

    def test_worker_independent_aggregation(self):
        """Fold must be interior-only and worker-independent."""
        _run_lbmverify("reduce")
