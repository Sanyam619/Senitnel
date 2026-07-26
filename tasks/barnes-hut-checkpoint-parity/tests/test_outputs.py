"""Hard macroscopic-invariant checks for the N-body campaign report.

Also drives the verifier-owned ``nbverify`` binary (staged and built by
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
CASE_ROOT = Path("/app/data/cases")
MANIFEST_ROOT = Path("/app/config/manifests")
NBVERIFY_BIN = Path("/app/bin/nbverify")

LABELS = ("plummer", "binary", "collapse")
WORKERS = (1, 2, 4)
MODES = ("cold", "resume")
ROW_KEYS = {
    "label",
    "workers",
    "mode",
    "energy",
    "momentum_L2",
    "mass",
    "stable",
}

PAIR_BAND = 1e-4
SPAN_BAND = 1e-3
MASS_BAND = 1e-2
# Manifest-governed plummer attractor floor (above build-meta path).
# Documented in /app/docs/report-schema.md under "Configuration authority"
# and "Physical bounds enforced by the verifier".
PLUMMER_ENERGY_FLOOR = 0.55


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


def mass0_for(label: str) -> float:
    doc = json.loads((CASE_ROOT / label / "particles.json").read_text())
    return float(sum(p["m"] for p in doc["particles"]))


class TestOutputs:
    def test_schema_surface(self):
        """Report exists with schema_tag, cases, parity, and exact row keys."""
        data = load_report()
        assert data["schema_tag"] == "nbody-campaign-v1"
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
            for key in ("energy", "momentum_L2", "mass"):
                val = float(row[key])
                assert val == val, f"{row['label']} {key} not finite"
                assert val not in (float("inf"), float("-inf")), (
                    f"{row['label']} {key} not finite"
                )

    def test_pair_gap_energy(self):
        """Cold vs resume energy relative gap stays within the schema band."""
        idx = rows_by()
        for label in LABELS:
            for w in WORKERS:
                cold = idx[(label, w, "cold")]
                resume = idx[(label, w, "resume")]
                assert rel_gap(cold["energy"], resume["energy"]) <= PAIR_BAND

    def test_pair_gap_mom(self):
        """Cold vs resume momentum_L2 relative gap stays within the schema band."""
        idx = rows_by()
        for label in LABELS:
            for w in WORKERS:
                cold = idx[(label, w, "cold")]
                resume = idx[(label, w, "resume")]
                assert (
                    rel_gap(cold["momentum_L2"], resume["momentum_L2"]) <= PAIR_BAND
                )

    def test_span_mass(self):
        """mass does not drift across worker counts for cold runs."""
        idx = rows_by()
        for label in LABELS:
            vals = [idx[(label, w, "cold")]["mass"] for w in WORKERS]
            assert rel_spread(vals) <= SPAN_BAND

    def test_span_mom(self):
        """momentum_L2 does not drift across worker counts for cold runs."""
        idx = rows_by()
        for label in LABELS:
            vals = [idx[(label, w, "cold")]["momentum_L2"] for w in WORKERS]
            assert rel_spread(vals) <= SPAN_BAND

    def test_integral_closed(self):
        """mass stays within the documented closure band of sum(particle masses)."""
        for row in load_report()["cases"]:
            target = mass0_for(row["label"])
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
                for key in ("energy", "momentum_L2", "mass"):
                    cold_resume = max(cold_resume, rel_gap(c[key], r[key]))
        worker_spread = 0.0
        for label in LABELS:
            for key in ("energy", "momentum_L2", "mass"):
                vals = [idx[(label, w, "cold")][key] for w in WORKERS]
                worker_spread = max(worker_spread, rel_spread(vals))
        assert abs(data["parity"]["cold_resume_max_rel"] - cold_resume) < 1e-9
        assert abs(data["parity"]["worker_spread_max_rel"] - worker_spread) < 1e-9
        assert data["parity"]["cold_resume_max_rel"] <= PAIR_BAND
        assert data["parity"]["worker_spread_max_rel"] <= SPAN_BAND

    def test_band_energy(self):
        """Plummer cold energy must sit on the manifest-governed attractor, not build-meta.

        The floor is a physical bound documented in /app/docs/report-schema.md
        (see 'Physical bounds enforced by the verifier') and referenced from
        the task instruction, so agents cannot be surprised by an undocumented
        threshold. This test also asserts the doc still carries the contract.
        """
        idx = rows_by()
        for w in WORKERS:
            row = idx[("plummer", w, "cold")]
            assert abs(row["energy"]) >= PLUMMER_ENERGY_FLOOR, (
                f"plummer cold w={w} |energy|={abs(row['energy']):.3e} < floor "
                f"{PLUMMER_ENERGY_FLOOR:.3e}; likely running under build-meta "
                "knobs instead of the manifest values"
            )
        text = SCHEMA_DOC.read_text()
        assert "cold_resume_max_rel" in text
        assert "1e-4" in text
        assert "plummer_energy_floor" in text, (
            "report-schema.md must document the plummer_energy_floor bound"
        )
        assert "0.55" in text, (
            "report-schema.md must document the numeric plummer |energy| floor "
            "(0.55) so agents see the physical bound"
        )
        assert "Configuration authority" in text, (
            "report-schema.md must document the manifest-vs-build authority "
            "rule under a 'Configuration authority' heading"
        )
        assert MANIFEST_ROOT.joinpath("plummer.toml").is_file()


def _run_nbverify(name: str) -> None:
    """Invoke the verifier-owned Go binary with the given subcommand."""
    assert NBVERIFY_BIN.is_file() and os.access(NBVERIFY_BIN, os.X_OK), (
        f"nbverify binary missing at {NBVERIFY_BIN}; conftest.py should have "
        "built it against the current /app sources"
    )
    result = subprocess.run(
        [os.fspath(NBVERIFY_BIN), name],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"nbverify {name} failed with exit {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            pytrace=False,
        )


class TestSubsystems:
    """Behavioral checks that exercise the internal packages directly.

    These tests invoke the verifier-owned nbverify binary built by
    conftest.py. The binary imports the current internal packages under
    /app and drives them with inputs the verifier picks, so a hand-written
    /output/campaign-report.json or a substituted run_campaign.sh cannot
    satisfy them without the underlying packages actually being correct.
    """

    def test_authority_selection(self):
        """Resolver must honor the manifest-derived blob."""
        _run_nbverify("policy")

    def test_checkpoint_round_trip(self):
        """Encode/Unpack must round-trip interior and primary-axis halo slots.

        Halo must be re-derived from current interior edges (west/east at the
        same depth), not copied from the pre-write ghost buffer. Contract is
        documented under 'Checkpoint / padded-state halo' in report-schema.md.
        """
        text = SCHEMA_DOC.read_text()
        assert "Checkpoint / padded-state halo" in text, (
            "report-schema.md must document the padded-state halo contract"
        )
        assert "ghost" in text.lower() and "interior" in text.lower()
        _run_nbverify("snap")

    def test_worker_independent_aggregation(self):
        """Fold must be interior-only and worker-independent."""
        _run_nbverify("reduce")
