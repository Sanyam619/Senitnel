"""Hard outcome checks for ambient-cap device broker cutover."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPORT = Path("/output/broker-cutover.json")
LAB = Path("/data/lab")
SEED = Path("/data/fixtures/broker-seed")
UNIT = LAB / "units" / "live.service"
DROPIN = LAB / "units" / "live.d" / "10-private.conf"
HOST_DEV = LAB / "mnt" / "host" / "dev"
BROKER_DEV = LAB / "mnt" / "broker" / "dev"
HOST_STALE = LAB / "mnt" / "host" / "stale"
FLEET = Path("/opt/broker/config/fleet-caps.conf")
NAMES = ("dev-alpha", "dev-beta", "dev-gamma")


def _expected_caps() -> str:
    text = FLEET.read_text(encoding="utf-8")
    m = re.search(r'capability_boundary\s*=\s*"([^"]+)"', text)
    assert m, "missing fleet capability_boundary"
    return m.group(1)


def _load() -> dict:
    assert REPORT.is_file(), f"missing {REPORT}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _by_name(payload: dict) -> dict[str, dict]:
    rows = payload.get("devices")
    assert isinstance(rows, list)
    out = {r["name"]: r for r in rows if isinstance(r, dict) and "name" in r}
    return out


def test_k3_zircon():
    """Ambient set must equal bounding bits after nested handoff."""
    want = _expected_caps()
    by_name = _by_name(_load())
    for name in NAMES:
        assert name in by_name, by_name.keys()
        row = by_name[name]
        amb = row.get("ambient_set")
        bound = row.get("bounding_set")
        assert isinstance(amb, str) and isinstance(bound, str), (name, type(amb), type(bound))
        assert amb == bound == want, (name, amb, bound, want)
        assert "," in amb
        assert "[" not in amb


def test_m8_obsidian():
    """Broker-owned nodes must live in the broker mount namespace."""
    by_name = _by_name(_load())
    seated = 0
    for name in NAMES:
        row = by_name[name]
        assert row.get("mount_ns") == "broker", row
        assert (BROKER_DEV / name).is_file(), name
        assert not (HOST_DEV / name).exists(), name
        seated += 1
    assert seated == 3
    assert (LAB / "identity" / "mnt_ns").read_text(encoding="utf-8").strip() == "broker"


def test_p2_garnet():
    """Post-cutover race must leave host stale markers cleared."""
    pulse = subprocess.run(
        ["/opt/broker/bin/racepulse"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert pulse.returncode == 0, pulse.stderr
    by_name = _by_name(_load())
    cleared = 0
    for name in NAMES:
        assert by_name[name].get("stale_cleared") is True, name
        assert not (HOST_STALE / name).exists(), name
        cleared += 1
    assert cleared == 3
    flag = (LAB / "race" / "last_pulse").read_text(encoding="utf-8").strip()
    assert flag == "clean"


def test_q7_topaz():
    """On-disk capability ledgers must agree with the active fleet boundary."""
    want = _expected_caps()
    bound_disk = (LAB / "caps" / "bounding").read_text(encoding="utf-8").strip()
    amb_disk = (LAB / "caps" / "ambient").read_text(encoding="utf-8").strip()
    eff_disk = (LAB / "caps" / "effective").read_text(encoding="utf-8").strip()
    assert amb_disk == bound_disk == eff_disk == want
    by_name = _by_name(_load())
    for name in NAMES:
        assert by_name[name]["bounding_set"] == bound_disk
        assert by_name[name]["ambient_set"] == amb_disk


def test_r1_onyx():
    """Merged unit policy must not contradict DeviceAllow."""
    live = UNIT.read_text(encoding="utf-8")
    drop = DROPIN.read_text(encoding="utf-8")
    assert "PrivateDevices=yes" not in live
    assert "PrivateDevices=yes" not in drop
    assert "PrivateDevices=no" in live
    assert "PrivateDevices=no" in drop
    assert live.count("DeviceAllow=") == 3
    for name in NAMES:
        assert f"char-{name}" in live


def test_t6_amber():
    """Ledger schema and broker-seed anchor must remain intact."""
    want = _expected_caps()
    payload = _load()
    assert payload.get("version") == 1
    devices = payload.get("devices")
    assert isinstance(devices, list) and len(devices) >= 3
    reported = {row.get("name") for row in devices if isinstance(row, dict)}
    assert set(NAMES).issubset(reported)
    matched = 0
    for row in devices:
        if row.get("name") not in NAMES:
            continue
        assert isinstance(row.get("name"), str)
        assert row.get("mount_ns") == "broker"
        assert row.get("ambient_set") == want
        assert row.get("bounding_set") == want
        assert row.get("stale_cleared") is True
        matched += 1
    assert matched == 3

    manifest = SEED / "checksums.sha256"
    assert manifest.is_file()
    checked = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        want_hash, rel = line.split(None, 1)
        rel = rel.strip().removeprefix("./")
        path = SEED / rel
        got = subprocess.run(
            ["sha256sum", str(path)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()[0]
        assert got == want_hash, rel
        checked += 1
    assert checked >= 4
