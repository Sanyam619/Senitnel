"""Verifier for ceph-osd-crush-reweight-seating.

EXPECTED values are re-derived from the digest-pinned fixtures under
/app/data/ (row mirror, out-journal, holds, epochs, device and group
specs). The desk entrypoint is re-invoked twice after clearing /output;
tests grade the emitted report plus the live end-state.
"""

import json
import subprocess
from pathlib import Path

import pytest

APP = Path("/app")
DATA = APP / "data"
VAR = Path("/var/lib/ceph/ops")
ETC = Path("/etc/ceph")
REPORT = Path("/output/crush-seat.json")
ENTRY = "/app/ops/run_crush_seat.sh"
SCHEMA_TAG = "crush-seat-v1"
HEALTH_TOKEN = "HEALTH_OK"


class Bundle:
    """Attribute bag for fixture-derived expectations."""

    def __init__(self, **fields):
        self.__dict__.update(fields)


def _is_true(value):
    return value is True


def _is_false(value):
    return value is False


# ---------------------------------------------------------------- fixtures --


def _epochs():
    vals = {}
    for line in (DATA / "ceph/epochs.toml").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            vals[key.strip()] = int(val.strip())
    return vals


def _standing_rows():
    """Newest-generation row per device from the pinned row mirror."""
    rows = {}
    for line in (DATA / "crush/crush_map.txt").read_text().splitlines():
        if not line.startswith("tip "):
            continue
        fields = dict(part.split("=", 1) for part in line.split()[1:])
        rows[int(fields["osd"])] = {
            "gen": int(fields["gen"]),
            "wm": int(fields["wm"]),
            "host": fields["host"],
        }
    return rows


def _journal_last_action():
    """Last action per device from the sealed out-journal, epoch order."""
    entries = []
    for line in (DATA / "ceph/out_journal.jsonl").read_text().splitlines():
        if line.strip():
            entries.append(json.loads(line))
    entries.sort(key=lambda row: row["epoch"])
    last = {}
    for row in entries:
        last[row["osd"]] = row["action"]
    return last


def _hold_hosts(clock):
    """(active, expired) hold hosts under strict until_epoch > clock."""
    active, expired = set(), set()
    for line in (DATA / "ceph/holds.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["until_epoch"] > clock:
            active.add(row["host"])
        else:
            expired.add(row["host"])
    return active, expired


def _pool_specs():
    pools = []
    for path in sorted((DATA / "ceph/pools").glob("*.toml")):
        spec = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if key == "name":
                spec[key] = val.strip('"')
            elif key in ("size", "pg_num"):
                spec[key] = int(val)
        pools.append(spec)
    return sorted(pools, key=lambda spec: spec["name"])


def expected_state():
    epochs = _epochs()
    rows = _standing_rows()
    last = _journal_last_action()
    active_holds, expired_holds = _hold_hosts(epochs["clock"])
    osds = []
    for dev in sorted(rows):
        row = rows[dev]
        up = row["gen"] >= epochs["floor"]
        seated = up and last.get(dev, "in") != "out"
        osds.append(
            {
                "id": dev,
                "host": row["host"],
                "weight": row["wm"] / 1000.0,
                "in": seated,
                "up": up,
                "generation": row["gen"],
            }
        )
    eligible = {o["host"] for o in osds if o["in"] and o["up"]} - active_holds
    pools = [
        {**spec, "degraded": len(eligible) < spec["size"]}
        for spec in _pool_specs()
    ]
    return Bundle(
        epochs=epochs,
        rows=rows,
        last=last,
        active_holds=active_holds,
        expired_holds=expired_holds,
        eligible=eligible,
        osds=osds,
        pools=pools,
    )


@pytest.fixture(scope="module")
def desk():
    """Clear /output, run the desk twice, capture both reports."""
    if REPORT.exists():
        REPORT.unlink()
    first = subprocess.run(
        ["bash", ENTRY], check=False, capture_output=True, text=True
    )
    assert first.returncode == 0, f"first pass failed: {first.stderr}"
    assert REPORT.exists(), "first pass emitted no report"
    bytes_one = REPORT.read_bytes()
    second = subprocess.run(
        ["bash", ENTRY], check=False, capture_output=True, text=True
    )
    assert second.returncode == 0, f"second pass failed: {second.stderr}"
    bytes_two = REPORT.read_bytes()
    return Bundle(
        one=bytes_one,
        two=bytes_two,
        report=json.loads(bytes_two.decode()),
        expected=expected_state(),
    )


def _report_osds(desk):
    return {o["id"]: o for o in desk.report["osds"]}


def _report_pools(desk):
    return {p["name"]: p for p in desk.report["pools"]}


def _sheet_milli(dev):
    text = (ETC / f"reweight.d/osd.{dev}.conf").read_text()
    for line in text.splitlines():
        if line.startswith("reweight_milli"):
            return int(line.partition("=")[2].strip())
    return None


# -------------------------------------------------------------------- tests --


def test_k2_agate(desk):
    """Report carries exactly the contract keys with correct types and
    seat_ok true after verifier re-entry."""
    report = desk.report
    assert set(report.keys()) == {"schema_tag", "osds", "pools", "seat_ok"}
    assert report["schema_tag"] == SCHEMA_TAG
    assert _is_true(report["seat_ok"])
    assert isinstance(report["osds"], list) and len(report["osds"]) == len(
        desk.expected.rows
    )
    for entry in report["osds"]:
        assert set(entry.keys()) == {
            "id",
            "host",
            "weight",
            "in",
            "up",
            "generation",
        }
        assert type(entry["id"]) is int
        assert isinstance(entry["host"], str)
        assert isinstance(entry["weight"], (int, float))
        assert not isinstance(entry["weight"], bool)
        assert isinstance(entry["in"], bool)
        assert isinstance(entry["up"], bool)
        assert type(entry["generation"]) is int
    assert isinstance(report["pools"], list) and len(report["pools"]) == len(
        desk.expected.pools
    )
    for entry in report["pools"]:
        assert set(entry.keys()) == {"name", "size", "pg_num", "degraded"}
        assert isinstance(entry["name"], str)
        assert type(entry["size"]) is int
        assert type(entry["pg_num"]) is int
        assert isinstance(entry["degraded"], bool)


def test_d5_basalt(desk):
    """Two consecutive seating passes emit byte-identical valid JSON with a
    trailing newline (no per-pass stamps)."""
    assert desk.one == desk.two, "seating passes are not byte-identical"
    assert desk.two.endswith(b"\n")
    json.loads(desk.one.decode())


def test_y8_gneiss(desk):
    """Frozen fixtures still match their pinned digests, sealed live copies
    equal their /app/data sources, and seat_ok rests on real sheet
    agreement with the durable standing rows."""
    pins = (APP / "packaging/fixtures.sha256").read_text().splitlines()
    assert pins, "fixture pin ledger is empty"
    verify = subprocess.run(
        ["sha256sum", "-c", str(APP / "packaging/fixtures.sha256")],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(DATA),
    )
    assert verify.returncode == 0, f"fixture drifted:\n{verify.stdout}"
    assert (VAR / "record.jsonl").read_bytes() == (
        DATA / "ceph/out_journal.jsonl"
    ).read_bytes()
    assert (VAR / "window.jsonl").read_bytes() == (
        DATA / "ceph/holds.jsonl"
    ).read_bytes()
    for dev, row in desk.expected.rows.items():
        assert _sheet_milli(dev) == row["wm"], f"live sheet {dev} disagrees"
    assert _is_true(desk.report["seat_ok"])


def test_r3_pumice(desk):
    """Per-device weight and up match the newest durable rows; the device
    whose standing generation sits below the floor reports up=false."""
    got = _report_osds(desk)
    floor = desk.expected.epochs["floor"]
    for want in desk.expected.osds:
        entry = got[want["id"]]
        assert abs(entry["weight"] - want["weight"]) < 1e-9, (
            f"device {want['id']} weight {entry['weight']} != {want['weight']}"
        )
        assert entry["up"] == want["up"], f"device {want['id']} up wrong"
    below = [
        dev
        for dev, row in desk.expected.rows.items()
        if row["gen"] < floor
    ]
    assert below, "fixture must carry a below-floor device"
    for dev in below:
        assert _is_false(got[dev]["up"])
        assert _is_false(got[dev]["in"])


def test_m6_schist(desk):
    """Out-journal continuity is last-action-by-epoch: an out followed by a
    later in is seated; an in followed by a later out is out yet still up."""
    got = _report_osds(desk)
    last = desk.expected.last
    rows = desk.expected.rows
    floor = desk.expected.epochs["floor"]
    returned = [
        dev
        for dev, action in last.items()
        if action == "in" and rows[dev]["gen"] >= floor
    ]
    pulled = [
        dev
        for dev, action in last.items()
        if action == "out" and rows[dev]["gen"] >= floor
    ]
    assert returned and pulled, "fixture must carry both continuity shapes"
    for dev in returned:
        assert _is_true(got[dev]["in"]), f"returned device {dev} reported out"
    for dev in pulled:
        assert _is_false(got[dev]["in"]), f"pulled device {dev} reported in"
        assert _is_true(got[dev]["up"]), f"pulled device {dev} must stay up"
    for want in desk.expected.osds:
        assert got[want["id"]]["in"] == want["in"]


def test_w4_marble(desk):
    """Pool degraded flags are recomputed from the seated host spread, not
    copied from the monitor annotations in the live group sheets."""
    got = _report_pools(desk)
    for want in desk.expected.pools:
        assert got[want["name"]]["degraded"] == want["degraded"], (
            f"pool {want['name']} degraded flag wrong"
        )


def test_h9_shale(desk):
    """An active hold excludes its host from placement while that host's
    devices stay in+up; an expired hold has no effect on the spread."""
    expected = desk.expected
    assert expected.active_holds, "fixture must carry an active hold"
    assert expected.expired_holds, "fixture must carry an expired hold"
    got_osds = _report_osds(desk)
    got_pools = _report_pools(desk)
    # Devices on the actively-held host stay in+up on their own standing.
    held_devs = [
        o["id"]
        for o in expected.osds
        if o["host"] in expected.active_holds and o["in"] and o["up"]
    ]
    assert held_devs, "fixture must seat devices on the held host"
    for dev in held_devs:
        assert _is_true(got_osds[dev]["in"])
        assert _is_true(got_osds[dev]["up"])
    # The held host is excluded from spread: the pool sized one past the
    # eligible host count is truthfully degraded.
    tight = [
        p for p in expected.pools if p["size"] > len(expected.eligible)
    ]
    assert tight, "fixture must carry a truthfully degraded pool"
    for pool in tight:
        assert _is_true(got_pools[pool["name"]]["degraded"])
    # The expired hold host still counts: pools within the eligible count
    # are not degraded.
    for pool in expected.pools:
        if pool["size"] <= len(expected.eligible):
            assert _is_false(got_pools[pool["name"]]["degraded"])


def test_c1_borax(desk):
    """After re-entry the state plane carries the seal receipt at the aim
    generation, gen.live equals the aim, and live sheets persist."""
    aim = desk.expected.epochs["target"]
    receipt = VAR / "state/apply.ok"
    assert receipt.exists(), "apply receipt missing after re-entry"
    fields = {}
    for line in receipt.read_text().splitlines():
        key, _, val = line.partition("=")
        fields[key.strip()] = val.strip()
    assert fields.get("gen") == str(aim)
    assert fields.get("mode") == "seal"
    live = (VAR / "state/gen.live").read_text().strip()
    assert live == str(aim)
    for dev, row in desk.expected.rows.items():
        assert _sheet_milli(dev) == row["wm"], (
            f"live sheet {dev} did not survive re-entry"
        )


def test_p5_ochre(desk):
    """Generation fields equal each device's newest durable row and the
    acceptance floor is inclusive at the boundary generation."""
    got = _report_osds(desk)
    floor = desk.expected.epochs["floor"]
    for want in desk.expected.osds:
        assert got[want["id"]]["generation"] == want["generation"], (
            f"device {want['id']} generation wrong"
        )
    boundary = [
        dev
        for dev, row in desk.expected.rows.items()
        if row["gen"] == floor
    ]
    assert boundary, "fixture must carry a boundary-generation device"
    for dev in boundary:
        assert _is_true(got[dev]["up"]), (
            f"floor is inclusive; device {dev} must be up"
        )


def test_t8_umber(desk):
    """The surface monitor still prints HEALTH_OK, and seat_ok=true is
    backed by deep sheet agreement rather than the monitor verdict."""
    probe = subprocess.run(
        ["/usr/local/bin/cephhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0
    assert HEALTH_TOKEN in probe.stdout
    # HEALTH_OK is not acceptance: seat_ok=true must be backed by real
    # sheet agreement with the durable standing rows.
    assert _is_true(desk.report["seat_ok"])
    for dev, row in desk.expected.rows.items():
        assert _sheet_milli(dev) == row["wm"], (
            "seat_ok is true without sheet agreement"
        )


def test_j4_lignite(desk):
    """The full osds array equals the end-state derived from the pinned
    fixtures across every field."""
    got = sorted(desk.report["osds"], key=lambda o: o["id"])
    want = desk.expected.osds
    assert len(got) == len(want)
    for have, need in zip(got, want):
        assert have["id"] == need["id"]
        assert have["host"] == need["host"]
        assert abs(have["weight"] - need["weight"]) < 1e-9
        assert have["in"] == need["in"]
        assert have["up"] == need["up"]
        assert have["generation"] == need["generation"]


def test_e2_galena(desk):
    """The full pools array equals the end-state derived from the pinned
    fixtures, and seat_ok couples to the emitted document."""
    got = sorted(desk.report["pools"], key=lambda p: p["name"])
    want = desk.expected.pools
    assert len(got) == len(want)
    for have, need in zip(got, want):
        assert have["name"] == need["name"]
        assert have["size"] == need["size"]
        assert have["pg_num"] == need["pg_num"]
        assert have["degraded"] == need["degraded"]
    assert _is_true(desk.report["seat_ok"])
