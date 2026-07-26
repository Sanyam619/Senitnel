"""Verifier for iscsi-alua-path-preference-cutover — domain seating outcomes."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPORT = Path("/output/alua-seat.json")
SEAT = Path("/app/ops/run_alua_seat.sh")
TRUTH = Path("/app/data/sysfs")
LEDGER = Path("/app/data/sysfs.sha256")
OPS = Path("/var/lib/multipath/ops")
BINDINGS = Path("/var/lib/multipath/bindings")
CONFD = Path("/etc/multipath/conf.d")
HEALTH = Path("/usr/local/bin/mpathhealth")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def _parse_list(path: Path, key: str) -> list[str]:
    if not path.is_file():
        return []
    m = re.search(rf"{key}\s*=\s*\[([^\]]*)\]", path.read_text())
    if not m:
        return []
    return [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]


def _roster() -> list[str]:
    return _parse_list(OPS / "roster.toml", "members")


def _authority(key: str) -> str:
    for line in (OPS / "authority.toml").read_text().splitlines():
        if line.startswith(key) and not line.startswith("surface_"):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError(f"missing {key} in authority.toml")


def _floor() -> int:
    return int(_authority("min_generation"))


def _holds() -> tuple[list[str], dict[str, int]]:
    src = OPS / "holds.toml"
    held = _parse_list(src, "held")
    until: dict[str, int] = {}
    in_until = False
    for line in src.read_text().splitlines():
        s = line.strip()
        if s.startswith("[until]"):
            in_until = True
            continue
        if s.startswith("[") and s != "[until]":
            in_until = False
            continue
        if in_until and "=" in s:
            k, v = s.split("=", 1)
            until[k.strip()] = int(v.strip())
    return held, until


def _fold() -> dict[str, int]:
    weights: dict[str, int] = {}
    for f in sorted(CONFD.glob("*.conf")):
        for line in f.read_text().splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[0] == "weight":
                weights[parts[1]] = int(parts[2])
    return weights


def _truth() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in TRUTH.glob("*.json"):
        d = json.loads(f.read_text())
        out[d["alias"]] = d
    return out


def _expected() -> tuple[dict[str, dict], dict[str, int]]:
    truth = _truth()
    fold = _fold()
    floor = _floor()
    held, until = _holds()
    seated: dict[str, dict] = {}
    for alias in _roster():
        if alias in held:
            continue
        d = truth[alias]
        pref = fold.get(alias)
        if pref is None:
            continue
        elig = [
            p
            for p in d["paths"]
            if p["alua"] == "active/optimized"
            and p["generation"] >= floor
            and p["group"] == pref
        ]
        if not elig:
            continue
        pick = min(elig, key=lambda p: (-p["prio"], p["dev"]))
        seated[d["wwid"]] = {
            "wwid": d["wwid"],
            "active_path": pick["dev"],
            "group": pick["group"],
            "priority": pick["prio"],
            "generation": pick["generation"],
        }
    held_wwids = {truth[a]["wwid"]: until.get(a, 0) for a in held}
    return seated, held_wwids


def _load_report() -> dict:
    assert REPORT.is_file(), "missing /output/alua-seat.json"
    return json.loads(REPORT.read_text())


def _live_bindings() -> dict[str, tuple[str, int]]:
    out: dict[str, tuple[str, int]] = {}
    if BINDINGS.is_file():
        for line in BINDINGS.read_text().splitlines():
            if not line.strip():
                continue
            wwid, dev, group = line.split()
            out[wwid] = (dev, int(group))
    return out


def _ao_paths_by_wwid() -> dict[str, set[str]]:
    """Map wwid -> set of AO path devices at/above the durable floor (truth)."""
    floor = _floor()
    out: dict[str, set[str]] = {}
    for d in _truth().values():
        out[d["wwid"]] = {
            p["dev"]
            for p in d["paths"]
            if p["alua"] == "active/optimized" and p["generation"] >= floor
        }
    return out


@pytest.fixture(scope="module", autouse=True)
def _seat_once() -> None:
    if not REPORT.is_file():
        _run(["bash", str(SEAT)], check=True)


def test_b3_cobalt() -> None:
    """Report exposes the required seating fields and value types."""
    doc = _load_report()
    assert isinstance(doc.get("schema_tag"), str) and doc["schema_tag"]
    assert isinstance(doc.get("path_ok"), bool)
    devices = doc.get("devices")
    assert isinstance(devices, list) and devices
    for row in devices:
        assert set(row) >= {"wwid", "active_path", "group", "priority", "generation"}
        assert isinstance(row["wwid"], str)
        assert isinstance(row["active_path"], str)
        assert isinstance(row["group"], int)
        assert isinstance(row["priority"], int)
        assert isinstance(row["generation"], int)
    holds = doc.get("holds")
    assert isinstance(holds, list)
    for row in holds:
        assert set(row) >= {"wwid", "until_epoch"}
        assert isinstance(row["wwid"], str)
        assert isinstance(row["until_epoch"], int)


def test_h7_nickel() -> None:
    """schema_tag equals the durable authority tag, not the surface tag."""
    doc = _load_report()
    assert doc["schema_tag"] == _authority("schema_tag")
    assert doc["schema_tag"] != "alua.seat.v1"


def test_k2_indium() -> None:
    """Seated devices match the durable AO active-path matrix exactly."""
    doc = _load_report()
    seated, _ = _expected()
    got = {r["wwid"]: r for r in doc["devices"]}
    assert set(got) == set(seated)
    for wwid, exp in seated.items():
        row = got[wwid]
        assert row["active_path"] == exp["active_path"]
        assert row["group"] == exp["group"]
        assert row["priority"] == exp["priority"]
        assert row["generation"] == exp["generation"]


def test_r5_carbon() -> None:
    """A map with an ANO decoy path seats the AO path, never the ANO one."""
    doc = _load_report()
    truth = _truth()
    a_wwid = truth["mpatha"]["wwid"]
    got = {r["wwid"]: r for r in doc["devices"]}
    assert a_wwid in got
    assert got[a_wwid]["active_path"] == "sdb"
    # sdi is active/non-optimized in the frozen fixtures — never a seated path.
    assert all(r["active_path"] != "sdi" for r in doc["devices"])


def test_t8_zinc() -> None:
    """Stale AO paths below the generation floor are never seated."""
    doc = _load_report()
    truth = _truth()
    b_wwid = truth["mpathb"]["wwid"]
    got = {r["wwid"]: r for r in doc["devices"]}
    assert b_wwid in got
    assert got[b_wwid]["active_path"] == "sdj"
    assert got[b_wwid]["active_path"] != "sdc"
    floor = _floor()
    assert all(r["generation"] >= floor for r in doc["devices"])


def test_m4_argon() -> None:
    """conf.d fold resolves preferred groups last-layer-wins."""
    gm = OPS / "group.map"
    assert gm.is_file(), "missing folded group map"
    got: dict[str, int] = {}
    for line in gm.read_text().splitlines():
        if line.strip():
            k, v = line.split()
            got[k] = int(v)
    expected = _fold()
    for alias in _roster():
        assert got.get(alias) == expected.get(alias)
    # The aborted-cutover overlay weights must not survive the fold.
    assert got["mpatha"] == 1
    assert got["mpathd"] == 1


def test_p6_xenon() -> None:
    """Priority and generation per seated map come from the chosen path."""
    doc = _load_report()
    seated, _ = _expected()
    got = {r["wwid"]: r for r in doc["devices"]}
    for wwid, exp in seated.items():
        assert got[wwid]["priority"] == exp["priority"]
        assert got[wwid]["generation"] == exp["generation"]
    assert all(r["priority"] > 0 for r in doc["devices"])


def test_w9_radon() -> None:
    """Held maps land in holds with their epoch and never in devices."""
    doc = _load_report()
    _, held_wwids = _expected()
    assert held_wwids, "expected at least one held map"
    got = {r["wwid"]: r["until_epoch"] for r in doc["holds"]}
    assert set(got) == set(held_wwids)
    for wwid, epoch in held_wwids.items():
        assert got[wwid] == epoch
    device_wwids = {r["wwid"] for r in doc["devices"]}
    assert not (device_wwids & set(held_wwids))


def test_c1_helium() -> None:
    """Runtime bindings seat exactly the expected active paths."""
    seated, _ = _expected()
    live = _live_bindings()
    assert set(live) == set(seated)
    for wwid, exp in seated.items():
        assert live[wwid] == (exp["active_path"], exp["group"])


def test_s2_neon() -> None:
    """path_ok is true and rests on durable preference, not surface health."""
    doc = _load_report()
    seated, _ = _expected()
    got = {r["wwid"]: (r["active_path"], r["group"]) for r in doc["devices"]}
    expect = {w: (r["active_path"], r["group"]) for w, r in seated.items()}
    assert got == expect
    assert doc["path_ok"] is True
    mode = (OPS / "prefer.toml").read_text()
    assert re.search(r'mode\s*=\s*"(durable|authority)"', mode)


def test_d7_boron() -> None:
    """Two seating runs produce byte-identical output."""
    first = REPORT.read_bytes()
    _run(["bash", str(SEAT)], check=True)
    second = REPORT.read_bytes()
    assert first == second


def test_f3_iron() -> None:
    """Clearing output and re-entering the entrypoint restores seating."""
    before = _load_report()
    REPORT.unlink()
    assert not REPORT.exists()
    _run(["bash", str(SEAT)], check=True)
    after = _load_report()
    seated, _ = _expected()
    got = {r["wwid"]: (r["active_path"], r["group"]) for r in after["devices"]}
    expect = {w: (r["active_path"], r["group"]) for w, r in seated.items()}
    assert got == expect
    assert after["path_ok"] is True
    assert after["schema_tag"] == before["schema_tag"]


def test_l8_sulfur() -> None:
    """Frozen remote-port fixtures keep their packaging digests."""
    proc = _run(["sha256sum", "-c", str(LEDGER)], check=False)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_v4_ozone() -> None:
    """Surface status can read ready while seating is graded on durable truth."""
    health = _run([str(HEALTH)], check=False)
    assert health.returncode == 0
    assert re.search(r"ready", health.stdout, re.IGNORECASE)
    doc = _load_report()
    seated, _ = _expected()
    got = {r["wwid"]: (r["active_path"], r["group"]) for r in doc["devices"]}
    expect = {w: (r["active_path"], r["group"]) for w, r in seated.items()}
    assert got == expect
    assert doc["path_ok"] is True


def test_n5_krypton() -> None:
    """Every seated path is an AO path at/above the floor; no standby/ANO."""
    doc = _load_report()
    ao = _ao_paths_by_wwid()
    for row in doc["devices"]:
        assert row["active_path"] in ao.get(row["wwid"], set())
