"""Session setup: re-run recovery from live admin state; require stable output.

Deletes agent-written /output artefacts, restores prebuilt bins on every pass,
seals /tests while the recovery entrypoint runs (so grade-time imports cannot
read expected values), runs the recovery entrypoint twice, and requires
byte-identical results. Hand-written /output that skips the toolchain cannot
survive this fixture.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

OUT = Path("/output")
REPORT = OUT / "reconciliation.json"
STAMP = OUT / "meta" / "run.stamp"
SNAPSHOT = Path("/var/log/fleet") / "recovery"
LOG_DIR = Path("/var/log/fleet")
BIN_DIR = Path("/app/bin")
REF_DIR = Path("/usr/lib/fleet/bin")
EPISODES_PIN = Path("/app/packaging/episodes.sha256")
TESTS_DIR = Path("/tests")
TESTS_HOLD = Path("/var/lib/fleet/.verifier_hold/tests")


def _fail(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
    pytest.exit(msg, returncode=1)


def _clean_output() -> None:
    if OUT.exists():
        for child in OUT.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


def _ensure_prebuilt() -> None:
    """Always restore image-shipped bins from the pinned restore copies."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("fleetctl", "yarder", "fleetpeek"):
        dest = BIN_DIR / name
        ref = REF_DIR / name
        if ref.is_file():
            shutil.copy2(ref, dest)
            dest.chmod(0o755)


def _seal_tests() -> None:
    """Clear /tests while the agent entrypoint runs so expected values are gone.

    Leaves the /tests directory itself in place (pytest cwd) but moves every
    child aside so grade-time imports of expected_for / restored digests fail.
    """
    if not TESTS_DIR.is_dir():
        return
    if TESTS_HOLD.exists():
        shutil.rmtree(TESTS_HOLD)
    TESTS_HOLD.mkdir(parents=True, exist_ok=True)
    for child in list(TESTS_DIR.iterdir()):
        dest = TESTS_HOLD / child.name
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        child.rename(dest)


def _unseal_tests() -> None:
    """Restore /tests contents after recovery passes so pytest can finish."""
    if not TESTS_HOLD.is_dir():
        return
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    for child in list(TESTS_HOLD.iterdir()):
        dest = TESTS_DIR / child.name
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        child.rename(dest)
    try:
        TESTS_HOLD.rmdir()
    except OSError:
        shutil.rmtree(TESTS_HOLD, ignore_errors=True)


def _assert_episode_pins() -> None:
    """Crash-export inputs must match packaging digests before grading."""
    import hashlib

    if not EPISODES_PIN.is_file():
        _fail(f"missing episode pin at {EPISODES_PIN}")
    for line in EPISODES_PIN.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        path = Path("/app") / rel
        if not path.is_file():
            _fail(f"missing pinned crash-export input {path}")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != digest:
            _fail(f"mutated crash-export input {path}")


def _run_pipeline(log_name: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / log_name
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            ["/bin/bash", "/app/ops/run_recovery.sh"],
            cwd="/app",
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if proc.returncode != 0:
        tail = ""
        if log_path.exists():
            tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-80:])
        _fail(f"recovery entrypoint failed ({proc.returncode}); see {log_path}\n{tail}")


def _snapshot(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(OUT, dest)


def _same_tree(a: Path, b: Path) -> bool:
    files_a = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    files_b = sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    if files_a != files_b:
        return False
    for rel in files_a:
        if (a / rel).read_bytes() != (b / rel).read_bytes():
            return False
    return True


@pytest.fixture(scope="session", autouse=True)
def fleet_recovery_session():
    entry = Path("/app/ops/run_recovery.sh")
    if not entry.is_file():
        _fail(f"missing recovery entrypoint at {entry}")
    _assert_episode_pins()
    _clean_output()
    _ensure_prebuilt()
    _seal_tests()
    try:
        _run_pipeline("run_recovery.sh")
        if not REPORT.is_file():
            _fail("recovery pass 1 did not write /output/reconciliation.json")
        if not STAMP.is_file():
            _fail("recovery pass 1 did not write /output/meta/run.stamp")
        _snapshot(SNAPSHOT)
        _clean_output()
        _ensure_prebuilt()
        _run_pipeline("run_recovery.sh")
        if not _same_tree(SNAPSHOT, OUT):
            _fail("two consecutive recovery runs produced divergent /output trees")
    finally:
        _unseal_tests()
    _assert_episode_pins()
    yield
