"""Session-scoped setup for the N-body campaign verifier.

The verifier must regenerate ``/output/campaign-report.json`` from the current
Go sources under ``/app`` before any test inspects it. Without this step a
fabricated report file left behind by an agent could satisfy the schema and
parity checks without the campaign ever being rebuilt or run.

The rebuild here compiles ``/app/cmd/campaign`` directly with ``go build`` and
then invokes the produced binary, rather than delegating to the agent-facing
``/app/scripts/run_campaign.sh`` entrypoint, so that any tampering with the
shell script cannot subvert the verifier.

In addition, a small verifier-owned Go program (``tests/gocheck/main.go``) is
copied into ``/app/cmd/nbverify/main.go`` on every session and built into
``/app/bin/nbverify``. It links against the current internal packages
(``policy``, ``snap``, ``reduce``, ``partition``) and exercises them with
verifier-controlled inputs, so a fabricated report or a doctored driver
script cannot mask defects the agent is expected to repair.

Kept in ``conftest.py`` (rather than ``tests/test.sh``) so the verifier script
stays on the offline pytest template enforced by the repo's static checks.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

APP_ROOT = Path("/app")
CAMPAIGN_PKG = "./cmd/campaign"
CAMPAIGN_BIN = APP_ROOT / "bin" / "campaign"
NBVERIFY_PKG = "./cmd/nbverify"
NBVERIFY_SRC = Path(__file__).resolve().parent / "gocheck" / "main.go"
NBVERIFY_DST_DIR = APP_ROOT / "cmd" / "nbverify"
NBVERIFY_DST = NBVERIFY_DST_DIR / "main.go"
NBVERIFY_BIN = APP_ROOT / "bin" / "nbverify"
REPORT_PATH = Path("/output/campaign-report.json")
LOG_DIR = Path("/logs/verifier")
BUILD_LOG = LOG_DIR / "campaign-build.log"
RUN_LOG = LOG_DIR / "campaign-run.log"
NBVERIFY_BUILD_LOG = LOG_DIR / "nbverify-build.log"


def _fail(msg: str) -> None:
    """Emit ``msg`` to stderr and abort the pytest session."""
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
def regenerate_campaign_report() -> None:
    """Rebuild the campaign binary and run it so the report matches live sources.

    Also stages and builds the verifier-owned ``nbverify`` binary so the
    behavioral tests can invoke it directly against the current internal
    packages.
    """
    if not (APP_ROOT / "cmd" / "campaign").is_dir():
        _fail(
            f"campaign package missing under {APP_ROOT}/cmd/campaign; cannot "
            "regenerate the report."
        )
    if not (APP_ROOT / "go.mod").is_file():
        _fail(f"go.mod missing under {APP_ROOT}; cannot rebuild the campaign.")
    if not NBVERIFY_SRC.is_file():
        _fail(f"verifier check source missing at {NBVERIFY_SRC}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CAMPAIGN_BIN.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REPORT_PATH.exists():
        REPORT_PATH.unlink()

    env = os.environ.copy()
    env.setdefault("GOCACHE", "/tmp/go-cache")
    env["CGO_ENABLED"] = "1"

    build_bin = os.fspath(CAMPAIGN_BIN)
    app_cwd = os.fspath(APP_ROOT)
    report_arg = os.fspath(REPORT_PATH)

    with BUILD_LOG.open("w", encoding="utf-8") as log:
        build = subprocess.run(
            ["go", "build", "-trimpath", "-o", build_bin, CAMPAIGN_PKG],
            cwd=app_cwd,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if build.returncode != 0:
        _fail(
            "campaign build failed with exit "
            f"{build.returncode}; see {BUILD_LOG}\n{_tail(BUILD_LOG)}"
        )
    if not CAMPAIGN_BIN.is_file() or not os.access(CAMPAIGN_BIN, os.X_OK):
        _fail(f"campaign binary missing or not executable at {CAMPAIGN_BIN}")

    with RUN_LOG.open("w", encoding="utf-8") as log:
        run = subprocess.run(
            [build_bin, report_arg],
            cwd=app_cwd,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if run.returncode != 0:
        _fail(
            "campaign driver failed with exit "
            f"{run.returncode}; see {RUN_LOG}\n{_tail(RUN_LOG)}"
        )
    if not REPORT_PATH.is_file() or REPORT_PATH.stat().st_size == 0:
        _fail(
            "campaign driver did not produce a non-empty "
            f"{REPORT_PATH}; see {RUN_LOG}\n{_tail(RUN_LOG)}"
        )

    NBVERIFY_DST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(NBVERIFY_SRC, NBVERIFY_DST)

    verify_bin = os.fspath(NBVERIFY_BIN)
    with NBVERIFY_BUILD_LOG.open("w", encoding="utf-8") as log:
        vbuild = subprocess.run(
            ["go", "build", "-trimpath", "-o", verify_bin, NBVERIFY_PKG],
            cwd=app_cwd,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if vbuild.returncode != 0:
        _fail(
            "nbverify build failed with exit "
            f"{vbuild.returncode}; see {NBVERIFY_BUILD_LOG}\n"
            f"{_tail(NBVERIFY_BUILD_LOG)}"
        )
    if not NBVERIFY_BIN.is_file() or not os.access(NBVERIFY_BIN, os.X_OK):
        _fail(f"nbverify binary missing or not executable at {NBVERIFY_BIN}")
