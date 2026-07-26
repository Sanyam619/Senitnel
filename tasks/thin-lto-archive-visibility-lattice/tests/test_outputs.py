"""Hard outcome checks for the thin-LTO archive visibility lattice."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROBE = "/app/bin/lattice_probe"
REPORT = Path("/output/lattice-report.json")
MATRIX = Path("/app/ops/matrix.toml")
PROBE_STAMP = Path("/app/ops/probe.stamp")

EXPECTED = {
    "alpha": {"vis_digest": 29895, "bitcode_epoch": 3, "archive_members": 4},
    "beta": {"vis_digest": 43497, "bitcode_epoch": 7, "archive_members": 6},
    "gamma": {"vis_digest": 41260, "bitcode_epoch": 7, "archive_members": 6},
    "delta": {"vis_digest": 41260, "bitcode_epoch": 7, "archive_members": 6},
    "epsilon": {"vis_digest": 23750, "bitcode_epoch": 5, "archive_members": 5},
}


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
    assert PROBE_STAMP.is_file(), "missing /app/ops/probe.stamp"
    digest = subprocess.run(
        ["sha256sum", PROBE],
        capture_output=True,
        text=True,
        check=False,
    )
    assert digest.returncode == 0, digest.stderr
    actual = digest.stdout.split()[0]
    expect = PROBE_STAMP.read_text().strip()
    assert actual == expect, "lattice_probe binary drift vs probe.stamp"


def _surfaces_agree(cell: dict) -> bool:
    sides = [cell["rust"], cell["go"], cell["c"], cell["header"]]
    dig = sides[0]["vis_digest"]
    epoch = sides[0]["bitcode_epoch"]
    return all(
        s["vis_digest"] == dig and s["bitcode_epoch"] == epoch for s in sides
    )


@pytest.fixture(scope="session")
def matrix_report() -> dict:
    _assert_harness_intact()
    assert Path(PROBE).exists(), "lattice_probe missing"
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
        f"lattice_probe did not write {REPORT}: rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    return json.loads(REPORT.read_text())


def test_k3_tier_alpha_ok(matrix_report: dict) -> None:
    """Ship strand_a cell must reach lattice ok."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)


def test_w9_tier_beta_ok(matrix_report: dict) -> None:
    """Fleet dual-strand cell must match EXPECTED epoch and digest."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["bitcode_epoch"] == EXPECTED["beta"]["bitcode_epoch"]
    assert cell["vis_digest"] == EXPECTED["beta"]["vis_digest"]


def test_m4_mark_alpha(matrix_report: dict) -> None:
    """Alpha digest/epoch/members must match EXPECTED and agree across surfaces."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["vis_digest"] == EXPECTED["alpha"]["vis_digest"]
    assert cell["bitcode_epoch"] == EXPECTED["alpha"]["bitcode_epoch"]
    assert cell["archive_members"] == EXPECTED["alpha"]["archive_members"]
    assert _surfaces_agree(cell)


def test_z2_mark_beta(matrix_report: dict) -> None:
    """Beta digest/epoch/members must match EXPECTED and agree across surfaces."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["vis_digest"] == EXPECTED["beta"]["vis_digest"]
    assert cell["bitcode_epoch"] == EXPECTED["beta"]["bitcode_epoch"]
    assert cell["archive_members"] == EXPECTED["beta"]["archive_members"]
    assert _surfaces_agree(cell)


def test_t6_span_gamma(matrix_report: dict) -> None:
    """Fleet strand_b release cell must carry correct epoch and digest."""
    cell = matrix_report["cells"]["gamma"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["bitcode_epoch"] == EXPECTED["gamma"]["bitcode_epoch"]
    assert cell["vis_digest"] == EXPECTED["gamma"]["vis_digest"]
    assert cell["archive_members"] == EXPECTED["gamma"]["archive_members"]


def test_n8_span_delta(matrix_report: dict) -> None:
    """Fleet strand_b packing and digest must match EXPECTED."""
    cell = matrix_report["cells"]["delta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["bitcode_epoch"] == EXPECTED["delta"]["bitcode_epoch"]
    assert cell["vis_digest"] == EXPECTED["delta"]["vis_digest"]
    assert cell["archive_members"] == EXPECTED["delta"]["archive_members"]
    assert cell["go"]["archive_members"] == cell["c"]["archive_members"]
    assert _surfaces_agree(cell)


def test_y1_tri_agree_beta(matrix_report: dict) -> None:
    """Beta rust/go/c/header digests and epochs must all agree at EXPECTED."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert _surfaces_agree(cell)
    assert cell["bitcode_epoch"] == EXPECTED["beta"]["bitcode_epoch"]
    assert cell["vis_digest"] == EXPECTED["beta"]["vis_digest"]


def test_f5_reentry_gamma(matrix_report: dict) -> None:
    """Re-running lattice_probe must keep gamma and epsilon coherent."""
    _ = matrix_report
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
        f"reentry probe failed: rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    again = json.loads(REPORT.read_text())
    gamma = again["cells"]["gamma"]
    assert gamma["status"] == "ok", gamma.get("error", gamma)
    assert gamma["bitcode_epoch"] == EXPECTED["gamma"]["bitcode_epoch"]
    assert gamma["vis_digest"] == EXPECTED["gamma"]["vis_digest"]
    assert gamma["archive_members"] == EXPECTED["gamma"]["archive_members"]
    assert _surfaces_agree(gamma)
    epsilon = again["cells"]["epsilon"]
    assert epsilon["status"] == "ok", epsilon.get("error", epsilon)
    assert epsilon["vis_digest"] == EXPECTED["epsilon"]["vis_digest"]
    assert epsilon["bitcode_epoch"] == EXPECTED["epsilon"]["bitcode_epoch"]
    assert _surfaces_agree(epsilon)


def test_v3_gate_reentry(matrix_report: dict) -> None:
    """After a successful report, re-probe must keep fleet/craft/epsilon cells coherent."""
    _ = matrix_report
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
        f"gate reentry probe failed: rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    again = json.loads(REPORT.read_text())
    for key in ("beta", "gamma", "delta", "epsilon"):
        cell = again["cells"][key]
        assert cell["status"] == "ok", cell.get("error", cell)
        assert cell["vis_digest"] == EXPECTED[key]["vis_digest"]
        assert cell["bitcode_epoch"] == EXPECTED[key]["bitcode_epoch"]
        assert cell["archive_members"] == EXPECTED[key]["archive_members"]


def test_p7_quota_alpha(matrix_report: dict) -> None:
    """Alpha archive membership must match ship packing count."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["archive_members"] == EXPECTED["alpha"]["archive_members"]
    assert cell["go"]["archive_members"] == EXPECTED["alpha"]["archive_members"]
    assert cell["c"]["archive_members"] == EXPECTED["alpha"]["archive_members"]


def test_h2_quota_beta(matrix_report: dict) -> None:
    """Beta archive membership must match fleet packing count."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["archive_members"] == EXPECTED["beta"]["archive_members"]
    assert cell["go"]["archive_members"] == EXPECTED["beta"]["archive_members"]
    assert cell["c"]["archive_members"] == EXPECTED["beta"]["archive_members"]


def test_q4_craft_epsilon(matrix_report: dict) -> None:
    """Novel craft cell must match EXPECTED (hardcode-audit killer)."""
    cell = matrix_report["cells"]["epsilon"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["vis_digest"] == EXPECTED["epsilon"]["vis_digest"]
    assert cell["bitcode_epoch"] == EXPECTED["epsilon"]["bitcode_epoch"]
    assert cell["archive_members"] == EXPECTED["epsilon"]["archive_members"]
    assert _surfaces_agree(cell)


def test_v6_rebuild_archctl(matrix_report: dict) -> None:
    """Durable /app/g5 sources must rebuild archctl (anti PATH-shim)."""
    _ = matrix_report
    out = Path("/tmp/vfy-archctl")
    proc = subprocess.run(
        ["go", "build", "-o", str(out), "."],
        cwd="/app/g5",
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.is_file()
    # Fleet resolve must stay on fleet after durable rebuild.
    got = subprocess.run(
        [str(out), "resolve", "fleet"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert got.returncode == 0
    assert got.stdout.strip() == "/app/config/profiles/fleet.toml"
