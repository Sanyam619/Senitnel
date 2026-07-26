"""Outcome checks for the proc-macro / cdylib host matrix."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROBE = "/app/bin/abi_probe"
REPORT = Path("/output/abi-matrix.json")
MATRIX = Path("/app/ops/matrix.toml")
PKG = Path("/app/pkg")
SHIP = Path("/app/config/profiles/ship.toml")

FROZEN_IDS = ["alpha", "beta", "gamma", "delta", "epsilon"]

# Verifier-owned expectations (not present in matrix.toml).
EXPECTED_TAGS = {
    "alpha": {"MG_CORE", "MG_LANE_X"},
    "beta": {"MG_CORE"},
    "delta": {"DY_CORE", "DY_LANE_Y"},
}


def _assert_harness_intact() -> None:
    """Refuse forged probes/matrices; ledger pins /app/bin/abi_probe and matrix.toml."""
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


def _cell_map(report: dict) -> dict[str, dict]:
    cells = report.get("cells", [])
    assert isinstance(cells, list), "cells must be an array"
    out = {}
    for c in cells:
        out[c["id"]] = c
    return out


def _run_probe() -> dict:
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


@pytest.fixture(scope="session")
def matrix_report() -> dict:
    return _run_probe()


def test_report_surface(matrix_report: dict) -> None:
    """Report schema is present and the feature-on cell carries gated tags."""
    assert matrix_report.get("schema_tag") == "abi-matrix-v1"
    cells = matrix_report.get("cells")
    assert isinstance(cells, list) and len(cells) >= 5
    for key in ("id", "status", "features", "profile", "artifact_kind", "version_tags"):
        assert key in cells[0], f"missing {key}"
    cmap = _cell_map(matrix_report)
    alpha = cmap["alpha"]
    assert alpha["status"] == "ok", alpha.get("error", alpha)
    assert EXPECTED_TAGS["alpha"] <= set(alpha["version_tags"])
    assert alpha["artifact_kind"] == "macro_surface"


def test_all_cells_ok(matrix_report: dict) -> None:
    """Every matrix cell must report status ok."""
    cmap = _cell_map(matrix_report)
    for cid in FROZEN_IDS:
        cell = cmap[cid]
        assert cell["status"] == "ok", f"{cid}: {cell.get('error', cell)}"


def test_feature_cell_symbols(matrix_report: dict) -> None:
    """Feature-on macro surface must expose the gated lane tag."""
    alpha = _cell_map(matrix_report)["alpha"]
    assert alpha["status"] == "ok", alpha.get("error", alpha)
    assert set(alpha["version_tags"]) == EXPECTED_TAGS["alpha"]


def test_feature_off_absent(matrix_report: dict) -> None:
    """Feature-off macro surface must omit the gated lane tag."""
    beta = _cell_map(matrix_report)["beta"]
    assert beta["status"] == "ok", beta.get("error", beta)
    tags = set(beta["version_tags"])
    assert tags == EXPECTED_TAGS["beta"]
    assert "MG_LANE_X" not in tags


def test_dual_load_disjoint(matrix_report: dict) -> None:
    """Dual-load tag_families must be present and disjoint."""
    eps = _cell_map(matrix_report)["epsilon"]
    assert eps["status"] == "ok", eps.get("error", eps)
    families = eps.get("tag_families")
    assert isinstance(families, dict)
    macro = set(families.get("macro_surface", []))
    cdylib = set(families.get("cdylib", []))
    assert "MG_CORE" in macro and "MG_LANE_X" in macro
    assert "DY_CORE" in cdylib and "DY_LANE_Y" in cdylib
    assert len(macro & cdylib) == 0, f"overlap: {macro & cdylib}"
    assert not any(t.startswith("MG_") for t in cdylib)
    assert not any(t.startswith("DY_") for t in macro)


def test_pc_names(matrix_report: dict) -> None:
    """Installed pkg-config metadata must name both split artifacts."""
    cmap = _cell_map(matrix_report)
    assert cmap["gamma"]["status"] == "ok", cmap["gamma"].get("error")
    assert list(PKG.glob("flux_macro*.pc")), "missing flux_macro pkg-config files"
    assert list(PKG.glob("flux_cdylib*.pc")), "missing flux_cdylib pkg-config files"
    assert (PKG / "flux_cdylib.release.pc").is_file()
    assert not (PKG / "flux_mono.pc").exists(), "legacy mono pc must not remain authoritative"


def test_release_pc_path(matrix_report: dict) -> None:
    """Release cell must resolve through the ship profile libdir suffix."""
    cmap = _cell_map(matrix_report)
    gamma = cmap["gamma"]
    assert gamma["status"] == "ok", gamma.get("error", gamma)
    assert gamma["artifact_kind"] == "cdylib"
    assert SHIP.is_file()
    ship_text = SHIP.read_text()
    assert 'libdir_suffix = "release"' in ship_text or "libdir_suffix=\"release\"" in ship_text
    release_pc = PKG / "flux_cdylib.release.pc"
    assert release_pc.is_file(), "missing flux_cdylib.release.pc"
    text = release_pc.read_text()
    assert "/app/pkg/lib/release" in text
    assert "/app/pkg/lib/debug" not in text
    assert "-lflux_cdylib" in text
    assert "-lflux_mono" not in text
    assert Path("/app/pkg/lib/release/libflux_cdylib.so").is_file()
    assert not (PKG / "flux_mono.pc").exists()


def test_probe_reentry(matrix_report: dict) -> None:
    """Re-running abi_probe keeps cells ok with disjoint families."""
    _ = matrix_report
    again = _run_probe()
    cmap = _cell_map(again)
    for cid in FROZEN_IDS:
        assert cmap[cid]["status"] == "ok", f"{cid}: {cmap[cid].get('error')}"
    eps = cmap["epsilon"]
    macro = set(eps["tag_families"]["macro_surface"])
    cdylib = set(eps["tag_families"]["cdylib"])
    assert len(macro & cdylib) == 0
    assert not (PKG / "flux_mono.pc").exists(), "mono rematerialized and was not cleared"


def test_matrix_ids_frozen(matrix_report: dict) -> None:
    """Stock matrix.toml must stay byte-pinned; seeded roster and profiles remain."""
    cmap = _cell_map(matrix_report)
    text = MATRIX.read_text()
    ids = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("id "):
            ids.append(line.split("=", 1)[1].strip().strip('"'))
    assert ids == FROZEN_IDS
    assert sorted(cmap) == sorted(FROZEN_IDS)
    assert 'profile = "dev"' in text
    assert 'profile = "release"' in text
    assert 'profile = "ship"' not in text
    assert 'profile = "field"' not in text
    assert "expect_tags" not in text
    assert "expect_symbols" not in text


def test_no_handwritten_bypass(matrix_report: dict) -> None:
    """A static forged report is overwritten by probe re-entry."""
    _ = matrix_report
    forged = {
        "schema_tag": "abi-matrix-v1",
        "cells": [
            {
                "id": cid,
                "status": "ok",
                "features": [],
                "profile": "dev",
                "artifact_kind": "forged",
                "version_tags": [],
            }
            for cid in FROZEN_IDS
        ],
    }
    REPORT.write_text(json.dumps(forged))
    assert list(PKG.glob("flux_cdylib*.pc")), "pc emission missing before re-entry"
    assert list(PKG.glob("flux_macro*.pc")), "macro pc emission missing before re-entry"
    again = _run_probe()
    cmap = _cell_map(again)
    assert cmap["epsilon"]["artifact_kind"] == "dual"
    assert "tag_families" in cmap["epsilon"]
    assert "DY_CORE" in cmap["epsilon"]["tag_families"]["cdylib"]
    assert cmap["gamma"]["artifact_kind"] == "cdylib"
    assert cmap["gamma"]["status"] == "ok"
    assert cmap["alpha"]["artifact_kind"] == "macro_surface"
    assert set(cmap["alpha"]["version_tags"]) == EXPECTED_TAGS["alpha"]
    assert set(cmap["delta"]["version_tags"]) == EXPECTED_TAGS["delta"]
    assert not (PKG / "flux_mono.pc").exists()
