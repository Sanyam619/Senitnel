"""Session-scoped setup for the merge pipeline verifier.

Regenerates ``/output/merge-report.json`` from the current Java sources
under ``/app`` before any test inspects it, so a fabricated report file
left behind by an agent cannot satisfy the checks without the pipeline
actually being correct.

The verifier also stages its own probe program under
``io.terminus.stitch.verify`` from ``tests/javacheck/Verify.java``, builds
it against the current sources, and exposes a helper that runs individual
subcommands. The probe imports the current pipeline packages directly, so
a doctored driver or a fabricated report cannot mask defects the
underlying components must repair.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

APP_ROOT = Path("/app")
SRC_ROOT = APP_ROOT / "src" / "main" / "java"
CLASSES_DIR = APP_ROOT / "build" / "classes"
BUILD_SH = APP_ROOT / "scripts" / "build.sh"
RUN_SH = APP_ROOT / "scripts" / "run_merge.sh"
REPORT_PATH = Path("/output/merge-report.json")

VERIFY_SRC = Path(__file__).resolve().parent / "javacheck" / "Verify.java"
VERIFY_DST_DIR = SRC_ROOT / "io" / "terminus" / "stitch" / "verify"
VERIFY_DST = VERIFY_DST_DIR / "Verify.java"

LOG_DIR = Path("/logs/verifier")
RUN_LOG = LOG_DIR / "merge-run.log"

_PROBE_PKG = "io.terminus.stitch" + ".verify"
_PROBE_FQN = _PROBE_PKG + ".Verify"


def _fail(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
    pytest.exit(msg, returncode=1)


def _tail(path: Path, limit: int = 200) -> str:
    if not path.exists():
        return ""
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:])
    except OSError:
        return ""


@pytest.fixture(scope="session", autouse=True)
def regenerate_merge_report() -> None:
    if not SRC_ROOT.is_dir():
        _fail(f"Java sources missing under {SRC_ROOT}; cannot rebuild the pipeline.")
    if not BUILD_SH.is_file():
        _fail(f"build script missing at {BUILD_SH}")
    if not RUN_SH.is_file():
        _fail(f"run script missing at {RUN_SH}")
    if not VERIFY_SRC.is_file():
        _fail(f"verifier probe source missing at {VERIFY_SRC}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REPORT_PATH.exists():
        REPORT_PATH.unlink()

    # Stage the verifier probe under the source tree so it compiles with
    # everything else against the current packages.
    VERIFY_DST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(VERIFY_SRC, VERIFY_DST)

    env = os.environ.copy()

    # Regenerate the report by driving the agent-facing runner. This calls
    # build.sh internally (rebuilding every source, including the staged
    # probe) and then invokes the merge driver.
    with RUN_LOG.open("w", encoding="utf-8") as log:
        run = subprocess.run(
            ["bash", os.fspath(RUN_SH)],
            cwd=os.fspath(APP_ROOT),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if run.returncode != 0:
        _fail(
            "merge pipeline run failed with exit "
            f"{run.returncode}; see {RUN_LOG}\n{_tail(RUN_LOG)}"
        )
    if not REPORT_PATH.is_file():
        _fail(
            f"pipeline produced no report at {REPORT_PATH}; see {RUN_LOG}\n"
            f"{_tail(RUN_LOG)}"
        )
    if not CLASSES_DIR.is_dir():
        _fail(f"expected compiled classes under {CLASSES_DIR} after run_merge.sh")


def run_verify(subcommand: str) -> None:
    """Invoke the verifier probe with the named subcommand."""
    result = subprocess.run(
        ["java", "-cp", os.fspath(CLASSES_DIR), _PROBE_FQN, subcommand],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Verify {subcommand} failed with exit {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def run_verify_fixture():
    return run_verify
