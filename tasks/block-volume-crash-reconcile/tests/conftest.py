"""Session-scoped verifier setup for the KVFS crash-recovery task.

Every pytest session:

* deletes ``/output/recovered_state.json`` and every ``/output/rebuilt_*.img``
  left by the agent, plus the compiled reconcile artefacts under
  ``/opt/kvfs/lib`` / ``/opt/kvfs/bin``;
* invokes ``/opt/kvfs/ops/run_recovery.sh`` twice from a clean tree and
  requires the two runs to produce byte-identical ``/output`` payloads
  (nondeterministic reconcilers fail here regardless of correctness);
* stages a verifier-owned probe under ``/tests/probe/verify_probe.c``,
  compiles it against the agent's freshly-built ``/opt/kvfs/lib/libkvfs.a``
  + ``/opt/kvfs/lib/m3_apply.o``, and runs it on the crash images. The
  probe's SHA-256 over the reconciled block image is compared against
  the verifier reference view so a fabricated JSON report or a
  hand-written ``/opt/kvfs/bin/reconcile`` that hard-codes correct payloads
  still trips the verifier if the underlying library is wrong.

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

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

KVFS_ROOT = Path("/opt/kvfs")
RECOVERY = KVFS_ROOT / "ops" / "run_recovery.sh"
OUTPUT_DIR = Path("/output")
LOG_DIR = Path("/logs/verifier")
REPORT = OUTPUT_DIR / "recovered_state.json"
REBUILT_GLOB = "rebuilt_*.img"

PROBE_SRC = Path("/tests/probe/verify_probe.c")
PROBE_BIN = Path("/tmp/kvfs-verify-probe")
PROBE_BUILD_LOG = "probe-build.log"

SNAPSHOT_DIR = Path("/tmp/kvfs-verifier-pass1")


def _fail(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
    pytest.exit(msg, returncode=1)


def _tail(path: Path, n: int = 200) -> str:
    if not path.exists():
        return ""
    try:
        return "\n".join(path.read_text(errors="replace").splitlines()[-n:])
    except OSError:
        return ""


def _clean_output() -> None:
    if REPORT.exists():
        REPORT.unlink()
    for img in OUTPUT_DIR.glob(REBUILT_GLOB):
        img.unlink()


def _clean_build() -> None:
    """Force a real rebuild from the agent's live sources.

    Stale ``.o`` files could otherwise mask a source-level regression:
    an agent that reverted a fix but forgot ``make clean`` would still
    ship a working binary until the next full build.
    """
    for stale in (
        KVFS_ROOT / "bin" / "reconcile",
        KVFS_ROOT / "lib" / "m3_apply.o",
        KVFS_ROOT / "lib" / "p7_sb.o",
        KVFS_ROOT / "lib" / "libkvfs.a",
    ):
        try:
            stale.unlink()
        except FileNotFoundError:
            pass


def _run_pipeline(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            ["/bin/bash", str(RECOVERY)],
            cwd=str(KVFS_ROOT),
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if proc.returncode != 0:
        _fail(
            f"run_recovery.sh failed with exit {proc.returncode}; "
            f"see {log_path}\n{_tail(log_path)}"
        )


def _build_probe() -> None:
    if not PROBE_SRC.is_file():
        _fail(f"missing verifier probe source at {PROBE_SRC}")
    lib_a = KVFS_ROOT / "lib" / "libkvfs.a"
    obj = KVFS_ROOT / "lib" / "m3_apply.o"
    if not lib_a.is_file() or not obj.is_file():
        _fail(
            "verifier probe cannot link: expected fresh "
            f"{obj} and {lib_a} from run_recovery.sh"
        )
    log_path = LOG_DIR / PROBE_BUILD_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            [
                "gcc",
                "-Wall",
                "-Wextra",
                "-std=c11",
                f"-I{KVFS_ROOT / 'include'}",
                str(PROBE_SRC),
                str(obj),
                str(lib_a),
                "-o",
                str(PROBE_BIN),
                "-lz",
                "-lcrypto",
                "-lssl",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if proc.returncode != 0:
        _fail(
            f"verifier probe build failed with exit {proc.returncode}; "
            f"see {log_path}\n{_tail(log_path)}"
        )
    if not PROBE_BIN.is_file() or not os.access(PROBE_BIN, os.X_OK):
        _fail(f"verifier probe missing or not executable at {PROBE_BIN}")


@pytest.fixture(scope="session", autouse=True)
def regenerate_recovery_outputs() -> None:
    if not RECOVERY.is_file() or not os.access(RECOVERY, os.X_OK):
        _fail(f"missing or non-executable {RECOVERY}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Pass 1: fresh regenerate into /output/.
    _clean_output()
    _clean_build()
    _run_pipeline(LOG_DIR / "recovery-pass1.log")

    if not REPORT.is_file() or REPORT.stat().st_size == 0:
        _fail(f"pipeline did not produce non-empty {REPORT}")
    rebuilt = sorted(OUTPUT_DIR.glob(REBUILT_GLOB))
    if not rebuilt:
        _fail("pipeline produced no rebuilt_*.img outputs")

    # Snapshot pass-1 output for the determinism cross-check.
    if SNAPSHOT_DIR.exists():
        shutil.rmtree(SNAPSHOT_DIR)
    SNAPSHOT_DIR.mkdir(parents=True)
    for src in [REPORT, *rebuilt]:
        shutil.copy2(src, SNAPSHOT_DIR / src.name)

    # Pass 2: re-run and compare byte-for-byte.
    _clean_output()
    _clean_build()
    _run_pipeline(LOG_DIR / "recovery-pass2.log")

    if not REPORT.is_file() or REPORT.stat().st_size == 0:
        _fail("pipeline pass 2 did not regenerate recovered_state.json")
    rebuilt_pass2 = sorted(OUTPUT_DIR.glob(REBUILT_GLOB))
    if {p.name for p in rebuilt_pass2} != {p.name for p in rebuilt}:
        _fail(
            "pipeline pass 2 produced a different set of rebuilt_*.img "
            f"outputs (pass1={[p.name for p in rebuilt]}, "
            f"pass2={[p.name for p in rebuilt_pass2]})"
        )
    for name in ("recovered_state.json", *[p.name for p in rebuilt]):
        first = (SNAPSHOT_DIR / name).read_bytes()
        second = (OUTPUT_DIR / name).read_bytes()
        if first != second:
            _fail(
                "nondeterministic reconciliation: pass-1 and pass-2 "
                f"disagree on {name} "
                f"({len(first)} vs {len(second)} bytes)"
            )

    # Build the verifier-owned probe from the freshly rebuilt agent library
    # so behavioral tests can exercise reconcile_b_image() directly.
    _build_probe()
