"""Hard outcome checks for the dual-cdylib host matrix."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROBE = "/app/bin/abi_probe"
REPORT = Path("/output/abi-matrix.json")
NOTES = Path("/app/link/abi_notes.toml")
MATRIX = Path("/app/ops/matrix.toml")


def _assert_harness_intact() -> None:
    ledger = Path(__file__).resolve().parent / "ledgers" / "harness.sha256"
    assert ledger.is_file(), f"missing ledger {ledger}"
    result = subprocess.run(
        ["sha256sum", "-c", str(ledger)],
        cwd="/",
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"harness integrity drift:\n{result.stdout}\n{result.stderr}"
        )


@pytest.fixture(scope="session")
def matrix_report() -> dict:
    _assert_harness_intact()
    assert Path(PROBE).exists(), "abi_probe missing"
    assert MATRIX.exists(), "matrix.toml missing"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    if REPORT.exists():
        REPORT.unlink()
    proc = subprocess.run(
        [PROBE],
        cwd="/app",
        text=True,
        capture_output=True,
        check=False,
    )
    assert REPORT.exists(), (
        f"abi_probe did not write {REPORT}: rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    return json.loads(REPORT.read_text())


def test_r3_tier_alpha_ok(matrix_report: dict) -> None:
    """Primary nuclide cell must link and load."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)


def test_v7_tier_beta_ok(matrix_report: dict) -> None:
    """Alt nuclide cell must link and load."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)


def test_j2_tagbag_alpha(matrix_report: dict) -> None:
    """Primary cell must expose NEXUS_2 for facet_a."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)
    versions = set(cell["symbol_versions"])
    assert "NEXUS_2" in versions
    assert "NEXUS_1" in versions


def test_h5_tagbag_beta(matrix_report: dict) -> None:
    """Alt cell must expose NEXUS_1B and omit facet_a-only NEXUS_2."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    versions = set(cell["symbol_versions"])
    assert "NEXUS_1B" in versions
    assert "NEXUS_2" not in versions


def test_p6_opt_dlopen(matrix_report: dict) -> None:
    """Release-profile cell must load through pkg-config metadata."""
    cell = matrix_report["cells"]["gamma"]
    assert cell["status"] == "ok", cell.get("error", cell)


def test_w4_cascade_delta_ok(matrix_report: dict) -> None:
    """Cascade cell must link and load with cx_ symbols."""
    cell = matrix_report["cells"]["delta"]
    assert cell["status"] == "ok", cell.get("error", cell)


def test_m9_cascade_tags(matrix_report: dict) -> None:
    """Cascade cell must expose CASCADE_1 and CASCADE_1C tags."""
    cell = matrix_report["cells"]["delta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    versions = set(cell["symbol_versions"])
    assert "CASCADE_1" in versions
    assert "CASCADE_1C" in versions
    assert "NEXUS_1" not in versions


def test_k3_dual_epsilon_ok(matrix_report: dict) -> None:
    """Dual-load cell must simultaneously load nuclide and cascade."""
    cell = matrix_report["cells"]["epsilon"]
    assert cell["status"] == "ok", cell.get("error", cell)


def test_f8_dual_partition(matrix_report: dict) -> None:
    """Dual-load cell nuclide/cascade version tags must be disjoint families."""
    cell = matrix_report["cells"]["epsilon"]
    assert cell["status"] == "ok", cell.get("error", cell)
    nuc_v = set(cell.get("nuclide_versions", []))
    cas_v = set(cell.get("cascade_versions", []))
    assert "NEXUS_1" in nuc_v
    assert "NEXUS_2" in nuc_v
    assert "CASCADE_1" in cas_v
    assert "CASCADE_1C" in cas_v
    assert len(nuc_v & cas_v) == 0, f"version overlap: {nuc_v & cas_v}"


def test_c8_meta_match(matrix_report: dict) -> None:
    """Report nuclide soname must match /app/link expectations."""
    assert matrix_report["nuclide_soname"] == "libnuclide.so.2"
    nuc_v = set(matrix_report["nuclide_versions"])
    assert "NEXUS_2" in nuc_v
