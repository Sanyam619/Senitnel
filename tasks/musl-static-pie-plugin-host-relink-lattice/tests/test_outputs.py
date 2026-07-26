"""Hard outcome checks for the musl static-PIE plugin lattice."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

PROBE_MAIN = Path("/app/tools/probe/main.go")
PROBE_MOD = Path("/app/tools/probe/go.mod")
REPORT = Path("/output/lattice-report.json")
CONTRACT = Path("/app/link/contract.toml")
MATRIX = Path("/app/ops/matrix.toml")
POLICY = Path("/app/link/cgo_policy.toml")

# Verifier-owned expectations. Do not read mutable /app/link/contract.toml for
# pass/fail values — that file is integrity-checked, but expected outcomes live
# here so rewriting the on-disk contract cannot green a fake report.
EXPECTED = {
    "alpha": {"tls_model": "global-dynamic", "plugin_abi": "v1"},
    "beta": {"tls_model": "global-dynamic", "plugin_abi": "v2"},
    "gamma": {"tls_model": "global-dynamic", "plugin_abi": "v1"},
    "delta": {"tls_model": "global-dynamic", "plugin_abi": "v1"},
    "epsilon": {"tls_model": "initial-exec", "plugin_abi": "v1"},
}

# Stock toolchain prefixes come from the image ENV (excludes writable /app/tools).
def _verifier_env() -> dict[str, str]:
    env = os.environ.copy()
    safe = env.get("LATTICE_SAFE_PATH")
    go_bin = env.get("GO_BIN")
    assert safe, "LATTICE_SAFE_PATH missing from verifier environment"
    assert go_bin, "GO_BIN missing from verifier environment"
    env["PATH"] = safe
    env["LATTICE_SAFE_PATH"] = safe
    env["GO_BIN"] = go_bin
    return env


def _assert_harness_intact() -> None:
    """Fail if the agent rewrote probe sources, matrix, contract, or cgo policy."""
    ledger = Path(__file__).resolve().parent.joinpath("ledgers").joinpath("harness.sha256")
    assert ledger.is_file(), f"missing ledger {ledger}"
    result = subprocess.run(
        ["sha256sum", "-c", str(ledger)],
        cwd="/",
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            "harness integrity drift (probe/matrix/contract/policy must stay intact):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    for path in (PROBE_MAIN, PROBE_MOD, MATRIX, CONTRACT, POLICY):
        assert path.is_file(), f"missing harness path {path}"


def _rebuild_probe_from_protected_sources() -> Path:
    """Rebuild the probe from ledger-checked sources into a verifier-only binary.

    The agent-facing /app/tools/lattice_probe is writable; running it would allow
    a forged reporter. Verifier rebuilds from sha256-protected sources instead,
    invoking GO_BIN under LATTICE_SAFE_PATH (image ENV; excludes /app/tools).
    """
    assert PROBE_MAIN.is_file() and PROBE_MOD.is_file(), "probe sources missing"
    src_dir = PROBE_MAIN.parent
    fd, raw_path = tempfile.mkstemp(prefix="tb3_")
    os.close(fd)
    out = Path(raw_path)
    out.unlink(missing_ok=True)
    env = _verifier_env()
    proc = subprocess.run(
        [env["GO_BIN"], "build", "-o", str(out), "."],
        cwd=str(src_dir),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode:
        raise AssertionError(
            "failed to rebuild lattice_probe from protected sources:\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    assert out.is_file(), "rebuilt lattice_probe missing"
    out.chmod(0o755)
    assert os.access(out, os.X_OK), "rebuilt lattice_probe is not executable"
    return out


@pytest.fixture(scope="session")
def matrix_report() -> dict:
    _assert_harness_intact()
    probe_bin = _rebuild_probe_from_protected_sources()
    assert MATRIX.is_file() and CONTRACT.is_file() and POLICY.is_file()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    if REPORT.exists():
        REPORT.unlink()
    proc = subprocess.run(
        [str(probe_bin)],
        cwd="/app",
        env=_verifier_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert REPORT.is_file(), (
        f"lattice_probe did not write {REPORT}: rc={proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    # Graded behavior comes from report contents, not the process exit code.
    payload = json.loads(REPORT.read_text())
    assert isinstance(payload.get("cells"), dict), payload
    return payload


def test_k2_tier_alpha_pass(matrix_report: dict) -> None:
    """Primary musl target cell must load."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["tls_model"] == EXPECTED["alpha"]["tls_model"]
    assert cell["plugin_abi"] == EXPECTED["alpha"]["plugin_abi"]


def test_m5_tier_beta_pass(matrix_report: dict) -> None:
    """Alt wide-frame cell must load."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["tls_model"] == EXPECTED["beta"]["tls_model"]
    assert cell["plugin_abi"] == EXPECTED["beta"]["plugin_abi"]


def test_r8_mode_match(matrix_report: dict) -> None:
    """Primary cell tls_model must match verifier-owned expectation."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["tls_model"] == EXPECTED["alpha"]["tls_model"]


def test_w3_frame_match(matrix_report: dict) -> None:
    """Alt cell plugin_abi must match verifier-owned expectation."""
    cell = matrix_report["cells"]["beta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["plugin_abi"] == EXPECTED["beta"]["plugin_abi"]


def test_n4_opt_tier_pass(matrix_report: dict) -> None:
    """Release/opt supervisor cell must load with expected fields."""
    cell = matrix_report["cells"]["gamma"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["tls_model"] == EXPECTED["gamma"]["tls_model"]
    assert cell["plugin_abi"] == EXPECTED["gamma"]["plugin_abi"]


def test_j7_supv_pass(matrix_report: dict) -> None:
    """Supervisor musl-target cell must load with expected fields."""
    cell = matrix_report["cells"]["delta"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["tls_model"] == EXPECTED["delta"]["tls_model"]
    assert cell["plugin_abi"] == EXPECTED["delta"]["plugin_abi"]


def test_q1_builder_lane(matrix_report: dict) -> None:
    """Glibc builder supervisor cell must stay on the builder tls_model."""
    cell = matrix_report["cells"]["epsilon"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["tls_model"] == EXPECTED["epsilon"]["tls_model"]
    assert cell["plugin_abi"] == EXPECTED["epsilon"]["plugin_abi"]


def test_v6_host_flag_observe(matrix_report: dict) -> None:
    """Primary host cell must expose musl CC and PIE stamps in observed flags."""
    cell = matrix_report["cells"]["alpha"]
    assert cell["status"] == "ok", cell.get("error", cell)
    flags = cell.get("flags")
    assert isinstance(flags, dict), "flags object missing from host cell report"
    cc = str(flags.get("CC", ""))
    pie = str(flags.get("PIE", ""))
    tls = str(flags.get("TLS_MODEL", ""))
    assert "musl-gcc" in cc, flags
    assert "-fPIE" in pie and "-pie" in pie, flags
    assert tls == EXPECTED["alpha"]["tls_model"], flags


def test_p9_builder_not_musl(matrix_report: dict) -> None:
    """Builder supervisor must not reuse the musl target tls_model."""
    cell = matrix_report["cells"]["epsilon"]
    assert cell["status"] == "ok", cell.get("error", cell)
    assert cell["tls_model"] == EXPECTED["epsilon"]["tls_model"]
    assert cell["tls_model"] != EXPECTED["alpha"]["tls_model"]
