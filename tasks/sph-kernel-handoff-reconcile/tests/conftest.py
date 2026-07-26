"""Session-scoped setup for the SPH handoff reconciliation verifier.

The verifier must regenerate ``/output/reconcile-report.json`` from the
current Rust sources under ``/app/ws`` before any test inspects it.
Without this step a fabricated report file left behind by an agent
could satisfy the schema checks without the runner ever being rebuilt
or run.

The rebuild here compiles the workspace directly with the Rust
toolchain and then invokes the produced ``sph-run`` binary, rather
than delegating to the agent-facing ``/app/scripts/run_reconcile.sh``
entrypoint, so that any tampering with the shell script cannot
subvert the verifier.

In addition, a small verifier-owned Rust program
(``tests/rustcheck/main.rs``) is copied over
``/app/ws/sph_verify/src/main.rs`` on every session and compiled with
the sph_verify workspace member. It links against the current
internal crates (``sph_a``, ``sph_d``, ``sph_b``,
``sph_c``, ``sph_kernels``, ``sph_core``) and exercises them
with verifier-controlled inputs, so a fabricated report or a doctored
driver script cannot mask defects the agent is expected to repair.

Kept in ``conftest.py`` (rather than ``tests/test.sh``) so the
verifier script stays on the offline pytest template enforced by the
repo's static checks.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

APP_ROOT = Path("/app")
WS_ROOT = APP_ROOT / "ws"
SPH_RUN_SRC_BIN = WS_ROOT / "target" / "release" / "sph-run"
SPH_RUN_DST_BIN = APP_ROOT / "bin" / "sph-run"
SPH_VERIFY_SRC_BIN = WS_ROOT / "target" / "release" / "sph-verify"
SPH_VERIFY_DST_BIN = Path("/logs/verifier/sph-verify")
RUSTCHECK_SRC = Path(__file__).resolve().parent / "rustcheck" / "main.rs"
SPH_VERIFY_MAIN_DST = WS_ROOT / "sph_verify" / "src" / "main.rs"
REPORT_PATH = Path("/output/reconcile-report.json")
LOG_DIR = Path("/logs/verifier")
BUILD_LOG = LOG_DIR / "sph-run-build.log"
RUN_LOG = LOG_DIR / "sph-run.log"
VERIFY_BUILD_LOG = LOG_DIR / "sph-verify-build.log"


def _fail(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
    pytest.exit(msg, returncode=1)


def _tail(path: Path, limit: int = 200) -> str:
    if not path.exists():
        return ""
    try:
        return "\n".join(
            path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
        )
    except OSError:
        return ""


@pytest.fixture(scope="session", autouse=True)
def regenerate_reconcile_report() -> None:
    """Rebuild the runner and verifier binaries from live sources.

    1. Discard any stale ``/output/reconcile-report.json`` so a
       fabricated file cannot satisfy the downstream checks.
    2. Overwrite ``/app/ws/sph_verify/src/main.rs`` from a verifier-
       owned copy so agent edits to that file are ignored.
    3. Build the whole workspace so ``sph-run`` and ``sph-verify``
       come from the current internal crates.
    4. Run ``sph-run`` to emit a fresh report.
    """
    if not WS_ROOT.is_dir():
        _fail(f"workspace missing at {WS_ROOT}; cannot rebuild the runner.")
    if not (WS_ROOT / "Cargo.toml").is_file():
        _fail(f"workspace Cargo.toml missing at {WS_ROOT}/Cargo.toml.")
    if not RUSTCHECK_SRC.is_file():
        _fail(f"verifier check source missing at {RUSTCHECK_SRC}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SPH_RUN_DST_BIN.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REPORT_PATH.exists():
        REPORT_PATH.unlink()

    SPH_VERIFY_MAIN_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(RUSTCHECK_SRC, SPH_VERIFY_MAIN_DST)

    env = os.environ.copy()
    cargo_home = env.get("CARGO_HOME", "/usr/local/cargo")
    rustup_home = env.get("RUSTUP_HOME", "/usr/local/rustup")
    env["CARGO_HOME"] = cargo_home
    env["RUSTUP_HOME"] = rustup_home
    env["PATH"] = f"{cargo_home}/bin:{rustup_home}/bin:" + env.get(
        "PATH", "/usr/bin:/bin"
    )
    cargo_bin = shutil.which("cargo", path=env["PATH"]) or f"{cargo_home}/bin/cargo"

    ws_cwd = os.fspath(WS_ROOT)
    with BUILD_LOG.open("w", encoding="utf-8") as log:
        build = subprocess.run(
            [cargo_bin, "build", "--release", "--locked", "--offline"],
            cwd=ws_cwd,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if build.returncode != 0:
        _fail(
            "workspace build failed with exit "
            f"{build.returncode}; see {BUILD_LOG}\n{_tail(BUILD_LOG)}"
        )
    if not SPH_RUN_SRC_BIN.is_file() or not os.access(SPH_RUN_SRC_BIN, os.X_OK):
        _fail(f"sph-run binary missing or not executable at {SPH_RUN_SRC_BIN}")
    if not SPH_VERIFY_SRC_BIN.is_file() or not os.access(SPH_VERIFY_SRC_BIN, os.X_OK):
        _fail(
            f"sph-verify binary missing or not executable at {SPH_VERIFY_SRC_BIN}; "
            f"see {BUILD_LOG}\n{_tail(BUILD_LOG)}"
        )
    shutil.copyfile(SPH_RUN_SRC_BIN, SPH_RUN_DST_BIN)
    shutil.copyfile(SPH_VERIFY_SRC_BIN, SPH_VERIFY_DST_BIN)
    os.chmod(SPH_RUN_DST_BIN, 0o755)
    os.chmod(SPH_VERIFY_DST_BIN, 0o755)

    with RUN_LOG.open("w", encoding="utf-8") as log:
        run = subprocess.run(
            [os.fspath(SPH_RUN_DST_BIN), os.fspath(REPORT_PATH)],
            cwd=os.fspath(APP_ROOT),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if run.returncode != 0:
        _fail(
            "sph-run failed with exit "
            f"{run.returncode}; see {RUN_LOG}\n{_tail(RUN_LOG)}"
        )
    if not REPORT_PATH.is_file() or REPORT_PATH.stat().st_size == 0:
        _fail(
            "sph-run did not produce a non-empty "
            f"{REPORT_PATH}; see {RUN_LOG}\n{_tail(RUN_LOG)}"
        )
