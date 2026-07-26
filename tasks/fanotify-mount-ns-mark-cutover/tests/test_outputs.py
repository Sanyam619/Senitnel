"""Hard outcome checks for fanotify mount-ns mark cutover."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/mark-cutover.json")
LAB = Path("/data/lab")
SEED = Path("/data/fixtures/watch-seed")
SEED_CHECKSUMS = Path("/tests/seed_checksums.sha256")
UNIT = LAB / "units" / "live.service"
HOST_MARKS = LAB / "marks" / "host"
BROKER_MARKS = LAB / "marks" / "broker"
HOST_TREE = LAB / "trees" / "host"
BROKER_TREE = LAB / "trees" / "broker"
HOST_JITTER = LAB / "race" / "jitter"
INHERIT_TABLE = LAB / "inherit" / "table"
INHERIT_OK = LAB / "inherit" / "ok"
POLICY_GEN = LAB / "identity" / "policy_gen"
MIGRATE_PATHS = ("path-alpha", "path-beta", "path-gamma", "path-delta")
# g3 roster order among movers
MIGRATE_ORDER = ("path-delta", "path-alpha", "path-gamma", "path-beta")
PINNED_PATHS = ("path-epsilon", "path-zeta")
ALL_PATHS = MIGRATE_PATHS + PINNED_PATHS


def _load() -> dict:
    assert REPORT.is_file(), f"missing {REPORT}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _by_path(payload: dict) -> dict[str, dict]:
    rows = payload.get("watches")
    assert isinstance(rows, list)
    return {r["path"]: r for r in rows if isinstance(r, dict) and "path" in r}


def test_v4_quartz():
    """Active generation is g3; migrate-tier paths exclusively in broker."""
    assert POLICY_GEN.read_text(encoding="utf-8").strip() == "g3"
    by_path = _by_path(_load())
    for name in MIGRATE_PATHS:
        assert name in by_path, by_path.keys()
        row = by_path[name]
        assert row.get("mark_ns") == "broker", (name, row)
        assert row.get("inherited_ok") is True, (name, row)
        assert (BROKER_MARKS / name).is_file(), name
        assert (BROKER_TREE / name).is_file(), name
        assert not (HOST_MARKS / name).exists(), name
        assert not (HOST_TREE / name).exists(), name


def test_w9_jasper():
    """All broker marks must be filesystem kind."""
    by_path = _by_path(_load())
    for name in MIGRATE_PATHS:
        row = by_path[name]
        assert row.get("mark_kind") == "filesystem", (name, row)
        kind = (BROKER_MARKS / name).read_text(encoding="utf-8").strip()
        assert kind == "filesystem", (name, kind)


def test_k6_fluorite():
    """Pinned-tier paths must remain exclusively in host namespace."""
    by_path = _by_path(_load())
    for name in PINNED_PATHS:
        assert name in by_path, by_path.keys()
        row = by_path[name]
        assert row.get("mark_ns") == "host", (name, row)
        assert row.get("mark_kind") == "inode", (name, row)
        assert row.get("inherited_ok") is False, (name, row)
        assert (HOST_TREE / name).is_file(), name
        assert (HOST_MARKS / name).is_file(), name
        assert not (BROKER_TREE / name).exists(), name
        assert not (BROKER_MARKS / name).exists(), name
        kind = (HOST_MARKS / name).read_text(encoding="utf-8").strip()
        assert kind == "inode", (name, kind)


def test_x2_citrine():
    """Inherit table must list movers only, in roster order, with remount-ok."""
    table = INHERIT_TABLE.read_text(encoding="utf-8").strip()
    assert table, "inherit table empty"
    ok = INHERIT_OK.read_text(encoding="utf-8").strip()
    assert ok == "1"
    entries = [e.strip() for e in table.split("\n") if e.strip()]
    assert entries == [f"{name}:remount-ok" for name in MIGRATE_ORDER], entries
    for name in PINNED_PATHS:
        assert name not in table, (name, table)


def test_y5_beryl():
    """Post-cutover race barrier must report clean with no jitter."""
    pulse = subprocess.run(
        ["/opt/fev/bin/racepulse"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert pulse.returncode == 0, pulse.stderr
    by_path = _by_path(_load())
    for name in ALL_PATHS:
        assert by_path[name].get("race_stable") is True, name
        assert not (HOST_JITTER / name).exists(), name
    flag = (LAB / "race" / "last_pulse").read_text(encoding="utf-8").strip()
    assert flag == "clean"


def test_z1_spinel():
    """No PrivateMounts=yes under units tree; ledger schema; seed untouched."""
    yes_hits = list(Path("/data/lab/units").rglob("*"))
    for path in yes_hits:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "PrivateMounts=yes" not in text, path
    main = UNIT.read_text(encoding="utf-8")
    assert "PrivateMounts=no" in main

    payload = _load()
    assert payload.get("version") == 1
    watches = payload.get("watches")
    assert isinstance(watches, list) and len(watches) >= 6
    reported = {row.get("path") for row in watches if isinstance(row, dict)}
    assert set(ALL_PATHS).issubset(reported)

    # Ground-truth digests live under /tests/ (verifier-only), not inside the
    # agent-writable seed tree, so re-signing the fixture cannot pass this check.
    assert SEED_CHECKSUMS.is_file(), f"missing verifier ledger {SEED_CHECKSUMS}"
    expected: dict[str, str] = {}
    for line in SEED_CHECKSUMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        want, rel = line.split(None, 1)
        rel = rel.strip().removeprefix("./")
        expected[rel] = want
    assert len(expected) == 13, f"verifier ledger size: {len(expected)}"

    present = {
        str(p.relative_to(SEED))
        for p in SEED.rglob("*")
        if p.is_file()
    }
    assert present == set(expected), (
        f"seed tree drift: extra={present - set(expected)} "
        f"missing={set(expected) - present}"
    )
    for rel, want in expected.items():
        path = SEED / rel
        got = subprocess.run(
            ["sha256sum", str(path)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()[0]
        assert got == want, rel


def test_h3_agate():
    """No dual-presence paths; inherit entries match broker tree population."""
    for name in ALL_PATHS:
        host_present = (HOST_TREE / name).exists()
        broker_present = (BROKER_TREE / name).exists()
        assert not (host_present and broker_present), f"dual presence: {name}"

    table = INHERIT_TABLE.read_text(encoding="utf-8").strip()
    entries = [e.strip() for e in table.split("\n") if e.strip()]
    assert len(entries) == 4, f"expected 4 entries, got {len(entries)}"
    assert entries == [f"{name}:remount-ok" for name in MIGRATE_ORDER], entries

    broker_files = {p.name for p in BROKER_TREE.iterdir() if p.is_file()}
    assert broker_files == set(MIGRATE_PATHS), f"broker tree mismatch: {broker_files}"
    host_files = {p.name for p in HOST_TREE.iterdir() if p.is_file()}
    assert host_files == set(PINNED_PATHS), f"host tree mismatch: {host_files}"
