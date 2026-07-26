"""Hard outcome checks for the triple-toolchain unify matrix."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROBE = "/app/bin/unify_probe"
REPORT = Path("/output/unify-report.json")
MATRIX = Path("/app/ops/matrix.toml")
PROBE_STAMP = Path("/app/ops/probe.stamp")
FLEET = Path("/app/config/profiles/fleet.toml")
STRAND = Path("/app/config/strand_m.toml")

# Verifier-owned EXPECTED (profile pack_width + facet/width stamp schedule).
# Stamp values match /app/data/fixtures/stamp_audit.jsonl; algebra is not
# published in instruction or the sealed probe binary.
EXPECTED = {
    "alpha": {"abi_stamp": 0xBEF1, "pack_width": 8},
    "beta": {"abi_stamp": 0xB2DF, "pack_width": 4},
    "gamma": {"abi_stamp": 0xB62E, "pack_width": 4},
    "delta": {"abi_stamp": 0xB62E, "pack_width": 4},
    "epsilon": {"abi_stamp": 0xB4DF, "pack_width": 8},
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
    assert actual == expect, "unify_probe binary drift vs probe.stamp"


def _surfaces_agree(cell: dict) -> bool:
    sides = [cell["rust"], cell["go"], cell["c"], cell["header"]]
    stamp = sides[0]["abi_stamp"]
    width = sides[0]["pack_width"]
    return all(s["abi_stamp"] == stamp and s["pack_width"] == width for s in sides)


def _strand_facet_y_enabled() -> bool:
    raw = STRAND.read_text()
    in_enable = False
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("["):
            in_enable = line == "[enable]"
            continue
        if not in_enable:
            continue
        if line.startswith("facet_y"):
            return "true" in line.lower()
    return False


@pytest.fixture(scope="session")
def matrix_report() -> dict:
    _assert_harness_intact()
    assert Path(PROBE).exists(), "unify_probe missing"
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
        f"unify_probe did not write {REPORT}: rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    return json.loads(REPORT.read_text())


# --- Per-cell status / stamp / width (anti-order opaque prefixes) ---


def test_k3_tier_alpha(matrix_report: dict) -> None:
    """Ship-only facet_x cell must unify."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)


def test_w9_tier_beta(matrix_report: dict) -> None:
    """Fleet dual-feature cell must unify at fleet EXPECTED width."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["pack_width"] == EXPECTED["beta"]["pack_width"]
    assert cell["abi_stamp"] == EXPECTED["beta"]["abi_stamp"]


def test_m4_mark_alpha(matrix_report: dict) -> None:
    """Alpha abi_stamp must match EXPECTED and agree across surfaces."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["abi_stamp"] == EXPECTED["alpha"]["abi_stamp"]
    assert cell["pack_width"] == EXPECTED["alpha"]["pack_width"]
    assert _surfaces_agree(cell)


def test_z2_mark_beta(matrix_report: dict) -> None:
    """Beta abi_stamp must match EXPECTED and agree across surfaces."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["abi_stamp"] == EXPECTED["beta"]["abi_stamp"]
    assert cell["pack_width"] == EXPECTED["beta"]["pack_width"]
    assert _surfaces_agree(cell)


def test_t6_span_gamma(matrix_report: dict) -> None:
    """Fleet facet_y release cell must carry correct pack_width."""
    cell = matrix_report["cells"]["gamma"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["pack_width"] == EXPECTED["gamma"]["pack_width"]
    assert cell["abi_stamp"] == EXPECTED["gamma"]["abi_stamp"]


def test_n8_span_delta(matrix_report: dict) -> None:
    """Fleet facet_y cell packing and stamp must match EXPECTED."""
    cell = matrix_report["cells"]["delta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["pack_width"] == EXPECTED["delta"]["pack_width"]
    assert cell["abi_stamp"] == EXPECTED["delta"]["abi_stamp"]
    assert cell["go"]["pack_width"] == cell["header"]["pack_width"]
    assert cell["c"]["pack_width"] == cell["header"]["pack_width"]
    assert _surfaces_agree(cell)


def test_e4_epsilon_ship(matrix_report: dict) -> None:
    """Ship dual-feature release cell must unify at ship EXPECTED stamp/width."""
    cell = matrix_report["cells"]["epsilon"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["pack_width"] == EXPECTED["epsilon"]["pack_width"]
    assert cell["abi_stamp"] == EXPECTED["epsilon"]["abi_stamp"]
    assert _surfaces_agree(cell)


# --- Cross-cell feature / width splits and release retention ---


def test_h8_release_facet(matrix_report: dict) -> None:
    """Gamma release cell must retain facet_y (strip mask must not clear it)."""
    cell = matrix_report["cells"]["gamma"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["abi_stamp"] == EXPECTED["gamma"]["abi_stamp"]
    assert cell["pack_width"] == EXPECTED["gamma"]["pack_width"]


def test_y1_tri_agree_beta(matrix_report: dict) -> None:
    """Beta rust/go/c/header stamps and widths must all agree at EXPECTED."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert _surfaces_agree(cell)
    assert cell["pack_width"] == EXPECTED["beta"]["pack_width"]
    assert cell["abi_stamp"] == EXPECTED["beta"]["abi_stamp"]


def test_q2_facet_split(matrix_report: dict) -> None:
    """Beta (fx+fy) stamp must differ from gamma (fy-only); catches wire off."""
    beta = matrix_report["cells"]["beta"]
    gamma = matrix_report["cells"]["gamma"]
    assert beta["status"] == "ok", beta.get("error", beta)
    assert gamma["status"] == "ok", gamma.get("error", gamma)
    assert beta["abi_stamp"] == EXPECTED["beta"]["abi_stamp"]
    assert gamma["abi_stamp"] == EXPECTED["gamma"]["abi_stamp"]
    assert beta["abi_stamp"] != gamma["abi_stamp"]


def test_p7_width_split(matrix_report: dict) -> None:
    """Ship pack_width must differ from fleet; catches uniform wrong width."""
    alpha = matrix_report["cells"]["alpha"]
    beta = matrix_report["cells"]["beta"]
    assert alpha["status"] == "ok", alpha.get("error", alpha)
    assert beta["status"] == "ok", beta.get("error", beta)
    assert alpha["pack_width"] == EXPECTED["alpha"]["pack_width"]
    assert beta["pack_width"] == EXPECTED["beta"]["pack_width"]
    assert alpha["pack_width"] != beta["pack_width"]


# --- Probe re-entry / durable gate (fleet width + strand enable) ---


def test_f5_reentry_gamma(matrix_report: dict) -> None:
    """Re-running unify_probe must keep gamma and epsilon coherent."""
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
    assert gamma["pack_width"] == EXPECTED["gamma"]["pack_width"]
    assert gamma["abi_stamp"] == EXPECTED["gamma"]["abi_stamp"]
    assert _surfaces_agree(gamma)
    epsilon = again["cells"]["epsilon"]
    assert epsilon["status"] == "ok", epsilon.get("error", epsilon)
    assert epsilon["pack_width"] == EXPECTED["epsilon"]["pack_width"]
    assert epsilon["abi_stamp"] == EXPECTED["epsilon"]["abi_stamp"]
    assert _surfaces_agree(epsilon)


def test_v3_gate_reentry(matrix_report: dict) -> None:
    """After a successful report, gate must still hold fleet width and facet_y."""
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
    for key in ("beta", "gamma", "epsilon"):
        cell = again["cells"][key]
        assert cell["status"] == "ok", cell.get("error", cell)
        assert cell["abi_stamp"] == EXPECTED[key]["abi_stamp"]
        assert cell["pack_width"] == EXPECTED[key]["pack_width"]
    fleet_raw = FLEET.read_text()
    assert "pack_width = 4" in fleet_raw, fleet_raw
    assert _strand_facet_y_enabled(), STRAND.read_text()
