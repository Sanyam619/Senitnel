"""Session-scoped setup for the elliptic-multigrid verifier.

The verifier must regenerate ``/app/output/`` from the current C sources
under ``/app`` before any test reads a JSON, trace, or field file. Without
this step a fabricated set of outputs left behind by an agent could
satisfy the schema and residual checks without the solver ever being
rebuilt or run.

The rebuild here compiles the binary directly with ``make`` from ``/app``
and then invokes the produced ``/app/elliptic_mg`` binary, rather than
delegating to the agent-facing ``/app/scripts/run_solve.sh`` entry point,
so any tampering with the shell script cannot subvert the verifier.

Kept in ``conftest.py`` (rather than ``tests/test.sh``) so the verifier
script stays on the offline pytest template enforced by the repo's static
checks.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

APP_ROOT = Path("/app")
BINARY = APP_ROOT / "elliptic_mg"
OUTPUT_DIR = APP_ROOT / "output"
LOG_DIR = Path("/logs/verifier")
BUILD_LOG = LOG_DIR / "elliptic-build.log"
RUN_LOG = LOG_DIR / "elliptic-run.log"


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
def regenerate_solver_outputs() -> None:
    """Rebuild the solver and run it so outputs match live sources."""
    if not (APP_ROOT / "Makefile").is_file():
        _fail(f"Makefile missing under {APP_ROOT}; cannot rebuild the solver.")
    if not (APP_ROOT / "src" / "main.c").is_file():
        _fail(f"src/main.c missing under {APP_ROOT}; cannot rebuild.")

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    (OUTPUT_DIR / "traces").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "fields").mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()

    with BUILD_LOG.open("w", encoding="utf-8") as log:
        clean = subprocess.run(
            ["make", "-C", os.fspath(APP_ROOT), "clean"],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if clean.returncode != 0:
            _fail(
                "make clean failed with exit "
                f"{clean.returncode}; see {BUILD_LOG}\n{_tail(BUILD_LOG)}"
            )
        build = subprocess.run(
            ["make", "-C", os.fspath(APP_ROOT)],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if build.returncode != 0:
        _fail(
            "solver build failed with exit "
            f"{build.returncode}; see {BUILD_LOG}\n{_tail(BUILD_LOG)}"
        )
    if not BINARY.is_file() or not os.access(BINARY, os.X_OK):
        _fail(f"solver binary missing or not executable at {BINARY}")

    with RUN_LOG.open("w", encoding="utf-8") as log:
        run = subprocess.run(
            [os.fspath(BINARY)],
            cwd=os.fspath(APP_ROOT),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if run.returncode != 0:
        _fail(
            "solver run failed with exit "
            f"{run.returncode}; see {RUN_LOG}\n{_tail(RUN_LOG)}"
        )
