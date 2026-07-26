"""Ops cutover outcome checks for ingest lease / mount seating."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPORT = Path("/output/lease-cutover.json")
ROOT = Path("/var/lib/ingest")
ETC = Path("/etc/ingest")
UNIT = ETC / "units" / "live.service"
DROPIN_DIR = ETC / "units" / "live.d"
ABORT = ETC / "units" / "abort.d" / "90-isolate.conf"
HOST_TEN = ROOT / "mnt" / "host" / "ten"
BROKER_TEN = ROOT / "mnt" / "broker" / "ten"
RING_BROKER = ROOT / "ring" / "broker"
LEASE_DURABLE = ROOT / "leases" / "durable"
JOURNAL_SEAL = ROOT / "journal" / "seal"
JOURNAL_PREFIX = ROOT / "journal" / "prefix"
JOURNAL_MODE = ROOT / "journal" / "cutover.mode"
ACTIVATION = ROOT / "meta" / "activation.toml"
CUTOVER_OK = ROOT / "meta" / "cutover.ok"
PREF_ARMED = ROOT / "meta" / "pref.armed"
SEAL_CAP = ETC / "fleet.seal"
WAL = ROOT / "journal" / "act.wal"
ROSTER = ETC / "tenant.roster"
SEED = ROOT / "fixtures" / "seed"
CUTOVER = "/app/ops/run_cutover.sh"
NAMES = ("ten-alpha", "ten-beta", "ten-gamma")
_SNAP_DIR: Path | None = None


def _read_cap() -> int:
    for line in SEAL_CAP.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return int(line)
    raise AssertionError("empty seal cap")


def _sealed_tip() -> tuple[int, str]:
    """Highest (gen,seq) tip with gen <= seal cap; must be seal mode."""
    cap = _read_cap()
    best: tuple[int, int, int, str, str] | None = None
    for line in WAL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue
        gen, seq = int(parts[0]), int(parts[1])
        if gen > cap:
            continue
        epoch, prefix, mode = int(parts[2]), parts[3], parts[4]
        if best is None or (gen, seq) > (best[0], best[1]):
            best = (gen, seq, epoch, prefix, mode)
    assert best is not None
    assert best[4] == "seal"
    return best[2], best[3]


def _roster() -> set[str]:
    names: set[str] = set()
    for line in ROSTER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.add(line)
    return names


def _want_seal(epoch: int, prefix: str) -> str:
    return f"seal:{epoch}:{prefix}"


def _load() -> dict:
    assert REPORT.is_file(), f"missing {REPORT}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _by_tenant(payload: dict) -> dict[str, dict]:
    rows = payload.get("tenants")
    assert isinstance(rows, list)
    return {r["tenant"]: r for r in rows if isinstance(r, dict) and "tenant" in r}


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _run_cutover() -> subprocess.CompletedProcess[str]:
    return _run([CUTOVER])


def _assert_units_open() -> None:
    live = UNIT.read_text(encoding="utf-8")
    assert "PrivateMounts=yes" not in live
    assert "PrivateMounts=no" in live
    drops = sorted(DROPIN_DIR.glob("*.conf"))
    assert len(drops) >= 2, drops
    for drop in drops:
        text = drop.read_text(encoding="utf-8")
        assert "PrivateMounts=yes" not in text, drop.name
        assert "PrivateMounts=no" in text, drop.name
    abort = ABORT.read_text(encoding="utf-8")
    assert "PrivateMounts=yes" not in abort
    assert "PrivateMounts=no" in abort


def _assert_seated() -> None:
    for name in NAMES:
        assert (BROKER_TEN / name).is_file(), name
        assert not (HOST_TEN / name).exists(), name
    assert (ROOT / "identity" / "mnt_ns").read_text(encoding="utf-8").strip() == "broker"


def _assert_durable_plane() -> None:
    want, prefix = _sealed_tip()
    assert LEASE_DURABLE.read_text(encoding="utf-8").strip() == str(want)
    assert JOURNAL_PREFIX.read_text(encoding="utf-8").strip() == prefix
    assert JOURNAL_SEAL.read_text(encoding="utf-8").strip() == _want_seal(want, prefix)
    assert JOURNAL_MODE.read_text(encoding="utf-8").strip() == "seal"
    assert CUTOVER_OK.read_text(encoding="utf-8").strip() == _want_seal(want, prefix)
    assert PREF_ARMED.read_text(encoding="utf-8").strip() == "seal"


def _ensure_cutover() -> None:
    if not REPORT.exists() or not (BROKER_TEN / "ten-alpha").is_file():
        cp = _run_cutover()
        assert cp.returncode == 0, f"cutover failed: {cp.stderr}\n{cp.stdout}"


def _snap() -> Path:
    global _SNAP_DIR
    if _SNAP_DIR is None:
        _SNAP_DIR = Path(tempfile.mkdtemp(prefix="iouring-lease-"))
    return _SNAP_DIR


def _snapshot() -> None:
    snap = _snap()
    root_snap = snap / "root"
    etc_snap = snap / "etc"
    if root_snap.exists():
        shutil.rmtree(root_snap)
    if etc_snap.exists():
        shutil.rmtree(etc_snap)
    shutil.copytree(ROOT, root_snap, dirs_exist_ok=True)
    shutil.copytree(ETC, etc_snap, dirs_exist_ok=True)
    if REPORT.is_file():
        shutil.copy2(REPORT, snap / REPORT.name)


def _restore() -> None:
    snap = _snap()
    root_snap = snap / "root"
    etc_snap = snap / "etc"
    if not root_snap.exists() or not etc_snap.exists():
        return
    if ROOT.exists():
        shutil.rmtree(ROOT)
    if ETC.exists():
        shutil.rmtree(ETC)
    shutil.copytree(root_snap, ROOT)
    shutil.copytree(etc_snap, ETC)
    report_snap = snap / REPORT.name
    if report_snap.is_file():
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(report_snap, REPORT)


def _reinject_private_yes() -> None:
    for path in [UNIT, *sorted(DROPIN_DIR.glob("*.conf")), ABORT]:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = path.read_text(encoding="utf-8") if path.exists() else "[Service]\n"
        text = text.replace("PrivateMounts=no", "PrivateMounts=yes")
        if "PrivateMounts=" not in text:
            text += "\nPrivateMounts=yes\n"
        path.write_text(text, encoding="utf-8")


def _parse_activation_tips(text: str) -> dict[str, str]:
    tips: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        tips[k.strip()] = v.strip().strip('"')
    return tips


def test_n4_quartz():
    """Roster tenants sit in the broker tree; host markers must be gone."""
    _ensure_cutover()
    by_name = _by_tenant(_load())
    for name in NAMES:
        assert name in by_name
        assert by_name[name].get("mount_ns") == "broker"
    _assert_seated()

    _snapshot()
    try:
        HOST_TEN.mkdir(parents=True, exist_ok=True)
        (HOST_TEN / "ten-alpha").write_text("bait", encoding="utf-8")
        cp = _run_cutover()
        assert cp.returncode == 0, cp.stderr
        _assert_seated()
    finally:
        _restore()


def test_p7_jasper():
    """Broker ring slots match sealed tip after cutover re-entry."""
    want, prefix = _sealed_tip()
    _ensure_cutover()
    by_name = _by_tenant(_load())
    gen = (RING_BROKER / "gen").read_text(encoding="utf-8").strip()
    assert gen == str(want), (gen, want)
    for name in NAMES:
        assert by_name[name].get("buf_fresh") is True
        body = (RING_BROKER / "slots" / name).read_text(encoding="utf-8").strip()
        assert body == f"{prefix}:{name}:{want}"

    _snapshot()
    try:
        (RING_BROKER / "gen").write_text("0", encoding="utf-8")
        (RING_BROKER / "slots" / "ten-beta").unlink(missing_ok=True)
        cp = _run_cutover()
        assert cp.returncode == 0, cp.stderr
        gen2 = (RING_BROKER / "gen").read_text(encoding="utf-8").strip()
        assert gen2 == str(want)
        for name in NAMES:
            body = (RING_BROKER / "slots" / name).read_text(encoding="utf-8").strip()
            assert body == f"{prefix}:{name}:{want}"
    finally:
        _restore()


def test_r2_citrine():
    """Durable lease/seal follow sealed journal tip; not harbor or drifted sheet."""
    want, prefix = _sealed_tip()
    _ensure_cutover()
    _assert_durable_plane()
    by_name = _by_tenant(_load())
    for name in NAMES:
        assert by_name[name].get("lease_epoch") == want
    # Beyond-cap drift tip must not win.
    assert prefix != "drift"
    assert want != 9

    _snapshot()
    try:
        LEASE_DURABLE.write_text("3", encoding="utf-8")
        JOURNAL_PREFIX.write_text("legacy", encoding="utf-8")
        JOURNAL_SEAL.write_text("seal:3", encoding="utf-8")
        JOURNAL_MODE.write_text("rollback", encoding="utf-8")
        PREF_ARMED.write_text("rollback", encoding="utf-8")
        CUTOVER_OK.unlink(missing_ok=True)
        cp = _run_cutover()
        assert cp.returncode == 0, cp.stderr
        _assert_durable_plane()
    finally:
        _restore()


def test_k8_fluorite():
    """Unit-policy fold + receipt clear isolation on live, live.d, and abort.d."""
    _ensure_cutover()
    _assert_units_open()

    _snapshot()
    try:
        _reinject_private_yes()
        CUTOVER_OK.unlink(missing_ok=True)
        (ROOT / "identity" / "mnt_ns").write_text("broker", encoding="utf-8")
        cp = _run_cutover()
        assert cp.returncode == 0, cp.stderr
        _assert_units_open()
        assert CUTOVER_OK.is_file()
    finally:
        _restore()


def test_w3_beryl():
    """Preflight stays stable; second cutover pass must not rematerialize harbor."""
    want, prefix = _sealed_tip()
    _ensure_cutover()
    before_dur = LEASE_DURABLE.read_text(encoding="utf-8").strip()
    before_gen = (RING_BROKER / "gen").read_text(encoding="utf-8").strip()
    before_seal = JOURNAL_SEAL.read_text(encoding="utf-8").strip()
    assert before_dur == str(want)
    assert before_gen == str(want)
    assert before_seal == _want_seal(want, prefix)

    pulse = _run(["/app/bin/preflight"])
    assert pulse.returncode == 0, pulse.stderr
    assert "stable" in pulse.stdout
    stamp = (ROOT / "preflight" / "last_run").read_text(encoding="utf-8").strip()
    assert stamp == "stable"

    cp = _run_cutover()
    assert cp.returncode == 0, cp.stderr
    after_dur = LEASE_DURABLE.read_text(encoding="utf-8").strip()
    after_gen = (RING_BROKER / "gen").read_text(encoding="utf-8").strip()
    after_seal = JOURNAL_SEAL.read_text(encoding="utf-8").strip()
    assert after_dur == before_dur == str(want)
    assert after_gen == before_gen == str(want)
    assert after_seal == before_seal == _want_seal(want, prefix)
    stamp2 = (ROOT / "preflight" / "last_run").read_text(encoding="utf-8").strip()
    assert stamp2 == "stable"

    by_name = _by_tenant(_load())
    for name in NAMES:
        row = by_name[name]
        assert row.get("preflight_stable") is True
        assert row.get("buf_slot") == f"{prefix}:{name}:{want}"
        assert row.get("mount_ns") == "broker"


def test_y6_spinel():
    """Ledger schema, activation roster-only tip map, and seed anchor must hold."""
    want, prefix = _sealed_tip()
    _ensure_cutover()
    payload = _load()
    assert payload.get("version") == 1
    by_name = _by_tenant(payload)
    assert set(by_name) == set(NAMES) == _roster()
    for name in NAMES:
        row = by_name[name]
        slot = row.get("buf_slot")
        assert isinstance(slot, str)
        assert slot == f"{prefix}:{name}:{want}"
        assert slot.count(":") == 2
        disk = (RING_BROKER / "slots" / name).read_text(encoding="utf-8").strip()
        assert slot == disk
        for key in (
            "tenant",
            "buf_slot",
            "mount_ns",
            "lease_epoch",
            "buf_fresh",
            "preflight_stable",
        ):
            assert key in row

    tips = _parse_activation_tips(ACTIVATION.read_text(encoding="utf-8"))
    assert set(tips) == set(NAMES)
    assert "omega" not in tips
    assert "ten-delta" not in tips
    for name in NAMES:
        assert tips[name] == f"{prefix}:{name}:{want}"

    manifest = SEED / "checksums.sha256"
    assert manifest.is_file()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(None, 1)
        rel = rel.lstrip("./")
        path = SEED / rel
        assert path.is_file(), rel
        got = subprocess.check_output(["sha256sum", str(path)], text=True).split()[0]
        assert got == digest, rel


def test_t6_amber():
    """Sequential cutover passes leave identical broker slots and open units."""
    want, prefix = _sealed_tip()
    _ensure_cutover()
    first = {
        name: (RING_BROKER / "slots" / name).read_text(encoding="utf-8").strip()
        for name in NAMES
    }
    cp = _run_cutover()
    assert cp.returncode == 0, cp.stderr
    second = {
        name: (RING_BROKER / "slots" / name).read_text(encoding="utf-8").strip()
        for name in NAMES
    }
    assert first == second
    for name in NAMES:
        assert second[name] == f"{prefix}:{name}:{want}"
    _assert_units_open()
    _assert_seated()
    stamp = (ROOT / "preflight" / "last_run").read_text(encoding="utf-8").strip()
    assert stamp == "stable"


def test_v4_jade():
    """Concurrent cutover jobs leave matching slots and clean dual residency."""
    want, prefix = _sealed_tip()
    _ensure_cutover()
    env = os.environ.copy()
    script = (
        "import os,subprocess,sys\n"
        "env=os.environ.copy()\n"
        "p1=subprocess.Popen([sys.argv[1]],env=env)\n"
        "p2=subprocess.Popen([sys.argv[1]],env=env)\n"
        "sys.exit(0 if p1.wait()==0 and p2.wait()==0 else 1)\n"
    )
    cp = subprocess.run(
        ["python3", "-c", script, CUTOVER],
        env=env,
        capture_output=True,
        text=True,
    )
    assert cp.returncode == 0, cp.stderr
    _assert_seated()
    _assert_units_open()
    _assert_durable_plane()
    for name in NAMES:
        body = (RING_BROKER / "slots" / name).read_text(encoding="utf-8").strip()
        assert body == f"{prefix}:{name}:{want}"
