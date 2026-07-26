"""Verifier for Squid ICP peer preference seating.

Re-enters /app/ops/run_squid_seat.sh and derives EXPECTED seating from
durable fixtures under /app/data and /var/lib/squid — not from agent
output alone.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/squid-seat.json")
DATA_PEERS = Path("/app/data/squid")
SITE = Path("/app/config/site_standard.conf")
ETC = Path("/etc/squid")
VAR = Path("/var/lib/squid")
OPS = VAR / "ops"
ROSTER = ETC / "roster.list"
ALLOWED_PREF = {"durable", "authority"}


def _parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _roster() -> list[str]:
    return [ln.strip() for ln in ROSTER.read_text().splitlines() if ln.strip()]


def _prefer_tip() -> dict[str, dict]:
    target = (VAR / "state" / "gen.target").read_text().strip()
    batches: list[dict] = []
    seal_ok = False
    for line in (VAR / "ops" / "prefer.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "seal" and str(row.get("gen")) == target:
            seal_ok = True
        if row.get("tag") == "batch":
            batches.append(row)
    assert seal_ok, "prefer journal missing seal for gen.target"
    chosen = None
    for batch in batches:
        if str(batch.get("gen")) != target:
            continue
        if batch.get("sealed") is True and batch.get("complete") is True:
            chosen = batch
    assert chosen is not None, "no sealed complete prefer batch"
    return {
        row["name"]: {
            "type": row["type"],
            "weight": int(row["weight"]),
            "generation": int(target),
        }
        for row in chosen["rows"]
    }


def _journal_eligible() -> set[str]:
    target = (VAR / "state" / "gen.target").read_text().strip()
    admitted: set[str] = set()
    revoked: set[str] = set()
    seal_ok = False
    for line in (VAR / "ops" / "peers.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "seal" and str(row.get("gen")) == target:
            seal_ok = True
        if str(row.get("gen")) != target:
            continue
        name = row.get("name")
        if not name:
            continue
        if row.get("tag") == "admit":
            admitted.add(str(name))
        elif row.get("tag") == "revoke":
            revoked.add(str(name))
    assert seal_ok
    return admitted - revoked


def _abort_set() -> set[str]:
    aborts: set[str] = set()
    for path in sorted((ETC / "conf.d").glob("*.cfg")):
        for raw in path.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line.startswith("abort="):
                continue
            val = line.split("=", 1)[1].strip()
            if val:
                aborts.add(val)
    return aborts


def _acl_fold() -> dict[str, str]:
    acl: dict[str, str] = {}
    for path in sorted((ETC / "conf.d").glob("*.cfg")):
        for raw in path.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line.startswith("acl.") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            acl[k.strip().split(".", 1)[1]] = v.strip()
    return acl


def _durable_host(name: str) -> str:
    fixture = DATA_PEERS / f"{name}.toml"
    for line in fixture.read_text().splitlines():
        if line.strip().startswith("host"):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError(f"missing host in {fixture}")


def _floor(name: str) -> int:
    return int((VAR / "floors" / f"{name}.floor").read_text().strip())


def _expected_peers() -> list[dict]:
    tip = _prefer_tip()
    eligible = _journal_eligible()
    aborted = _abort_set()
    rows = []
    for name in _roster():
        t = tip[name]
        selected = (
            name in eligible
            and name not in aborted
            and t["generation"] >= _floor(name)
        )
        rows.append(
            {
                "name": name,
                "host": _durable_host(name),
                "type": t["type"],
                "weight": t["weight"],
                "generation": t["generation"],
                "selected": selected,
            }
        )
    return rows


def _expected_acls() -> list[dict]:
    fold = _acl_fold()
    return [
        {"name": name, "matched": fold[name] == "match"}
        for name in sorted(fold)
    ]


def _prefer_mode() -> str:
    text = (OPS / "prefer.toml").read_text()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("mode"):
            return line.split("=", 1)[1].strip().strip('"')
    return "live"


def _reseat() -> dict:
    REPORT.unlink(missing_ok=True)
    proc = subprocess.run(
        ["/bin/bash", "/app/ops/run_squid_seat.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/squid-seat.json"
    return json.loads(REPORT.read_text())


def test_q3_topaz():
    """Ledger schema, schema_tag, seat_ok, and selected polarity after seating."""
    doc = _reseat()
    assert doc["schema_tag"] == "squid-seat-v1"
    assert isinstance(doc["peers"], list)
    assert isinstance(doc["acls"], list)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"] is True
    needed = {"name", "host", "type", "weight", "generation", "selected"}
    for row in doc["peers"]:
        assert needed <= set(row)
        assert isinstance(row["weight"], int)
        assert isinstance(row["generation"], int)
        assert isinstance(row["selected"], bool)
        assert row["type"] in {"parent", "sibling"}
        assert not row["host"].startswith("10.")
    for row in doc["acls"]:
        assert {"name", "matched"} <= set(row)
        assert isinstance(row["matched"], bool)
    by_name = {p["name"]: p for p in doc["peers"]}
    assert by_name["north"]["selected"] is True
    assert by_name["south"]["selected"] is False
    assert by_name["core"]["selected"] is False
    assert _prefer_mode() in ALLOWED_PREF
    bind = _parse_kv((OPS / "tip_bind.accept").read_text())
    assert bind.get("gen") == (VAR / "state" / "gen.target").read_text().strip()


def test_n4_beryl():
    """Two seating runs leave byte-identical ledger bytes."""
    _reseat()
    first = REPORT.read_bytes()
    _reseat()
    second = REPORT.read_bytes()
    assert first == second
    assert first.endswith(b"\n")
    assert (VAR / "state" / "gen.live").read_text().strip() == (
        VAR / "state" / "gen.target"
    ).read_text().strip()


def test_w7_quartz():
    """Frozen peer fixtures stay aligned after a successful durable seat."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    by_name = {p["name"]: p for p in doc["peers"]}
    tip = _prefer_tip()
    for name in _roster():
        fixture = DATA_PEERS / f"{name}.toml"
        assert fixture.is_file(), name
        text = fixture.read_text()
        assert f'name = "{name}"' in text
        host = _durable_host(name)
        durable = (VAR / "peers" / f"{name}.host").read_text().strip()
        assert host == durable
        assert host.startswith("127.0.0.")
        assert f'host = "{host}"' in text
        tip_type = (VAR / "state" / f"tip_{name}.type").read_text().strip()
        tip_weight = int((VAR / "state" / f"tip_{name}.weight").read_text().strip())
        assert tip_type == tip[name]["type"]
        assert tip_weight == tip[name]["weight"]
        assert by_name[name]["type"] == tip_type
        assert by_name[name]["weight"] == tip_weight


def test_v5_coral():
    """Sealed complete prefer tip beats incomplete later tip weights."""
    doc = _reseat()
    by_name = {p["name"]: p for p in doc["peers"]}
    assert by_name["core"]["weight"] == 70
    assert by_name["core"]["weight"] != 200
    assert by_name["north"]["type"] == "parent"
    assert by_name["north"]["weight"] == 100
    assert by_name["west"]["type"] == "sibling"
    assert by_name["west"]["weight"] == 90


def test_p9_jade():
    """Revoked journal peer is never selected."""
    doc = _reseat()
    by_name = {p["name"]: p for p in doc["peers"]}
    assert by_name["south"]["selected"] is False
    assert "south" not in _journal_eligible()


def test_h8_amber():
    """Abort package stays forensic while live drop-in is site-standard."""
    _reseat()
    abort_kv = _parse_kv((VAR / "ops" / "abort.d" / "90-local.cfg").read_text())
    live_kv = _parse_kv((ETC / "conf.d" / "90-local.cfg").read_text())
    site_kv = _parse_kv(SITE.read_text())
    assert abort_kv.get("tip_policy") == "prefer_abort"
    assert abort_kv.get("weight.core") == "999"
    assert live_kv.get("tip_policy") == "prefer_icp"
    assert live_kv.get("tip_policy") == site_kv["tip_policy"]
    assert live_kv.get("bind_order") == site_kv["bind_order"]
    for key, val in site_kv.items():
        if key.startswith("acl."):
            assert live_kv.get(key) == val
    assert live_kv != abort_kv
    assert "weight.core" not in live_kv or live_kv.get("weight.core") != "999"


def test_c1_flint():
    """Matching cutover receipt skips rematerialize; live drop-in remains."""
    _reseat()
    receipt = VAR / "state" / "cutover.ok"
    assert receipt.is_file()
    rkv = _parse_kv(receipt.read_text())
    target = (VAR / "state" / "gen.target").read_text().strip()
    assert rkv.get("gen") == target
    assert rkv.get("mode") == "seal"
    live = ETC / "conf.d" / "90-local.cfg"
    assert live.is_file()
    assert live.read_text().strip()
    receipt.write_text("gen=3\nmode=live\n")
    _reseat()
    live_after = _parse_kv(live.read_text())
    assert (VAR / "ops" / "abort.d" / "90-local.cfg").is_file()
    assert live_after.get("tip_policy") == "prefer_icp"


def test_r6_slate():
    """ACL abort set excludes core; north and west remain selectable."""
    doc = _reseat()
    by_name = {p["name"]: p for p in doc["peers"]}
    assert "core" in _abort_set()
    assert by_name["core"]["selected"] is False
    assert by_name["north"]["selected"] is True
    assert by_name["west"]["selected"] is True


def test_j2_onyx():
    """Folded ACL matched flags follow last-writer site-standard tokens."""
    doc = _reseat()
    acls = {a["name"]: a["matched"] for a in doc["acls"]}
    assert acls.get("allow_icp") is True
    assert acls.get("deny_core") is True
    assert acls.get("lab_window") is False
    expected = {a["name"]: a["matched"] for a in _expected_acls()}
    assert acls == expected


def test_m1_opal():
    """Full roster matrix matches durable tip × journal × floor × abort."""
    doc = _reseat()
    assert doc["peers"] == _expected_peers()
    assert doc["seat_ok"] is True


def test_u2_mica():
    """East sits below durable floor; incomplete tip must not seat it."""
    doc = _reseat()
    by_name = {p["name"]: p for p in doc["peers"]}
    assert by_name["east"]["generation"] == 7
    assert _floor("east") == 8
    assert by_name["east"]["selected"] is False
    assert by_name["east"]["type"] == "parent"
    assert by_name["east"]["weight"] == 80


def test_k5_garnet():
    """Live peer sheets carry tip type/weight and durable hosts."""
    doc = _reseat()
    for row in doc["peers"]:
        sheet = _parse_kv((ETC / "peers.d" / f"{row['name']}.peer").read_text())
        assert sheet["type"] == row["type"]
        assert int(sheet["weight"]) == row["weight"]
        assert sheet["host"] == row["host"]
        assert sheet["host"] == _durable_host(row["name"])
        assert not sheet["host"].startswith("10.")
        if row["name"] == "north":
            assert sheet["type"] != "sibling" or row["type"] == "sibling"
            assert int(sheet["weight"]) == 100
        if row["name"] == "core":
            assert int(sheet["weight"]) != 999


def test_t4_pearl():
    """Surface squidhealth ready is not sufficient without durable seat matrix."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    assert doc["peers"] == _expected_peers()
    proc = subprocess.run(
        ["/usr/local/bin/squidhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "ready" in proc.stdout.lower()


def test_s8_zircon():
    """Clearing the ledger and reseating reconstitutes the same matrix."""
    _reseat()
    REPORT.unlink(missing_ok=True)
    (VAR / "state" / "selected.set").write_text("")
    doc = _reseat()
    assert doc["peers"] == _expected_peers()
    assert doc["seat_ok"] is True


def test_y3_jasper():
    """Preference must be durable/authority and survive stock re-entry."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    assert _prefer_mode() in ALLOWED_PREF
    tip = _prefer_tip()
    for name in _roster():
        assert (VAR / "state" / f"tip_{name}.type").read_text().strip() == tip[name]["type"]
        sheet = _parse_kv((ETC / "peers.d" / f"{name}.peer").read_text())
        assert sheet["host"] == _durable_host(name)
        assert int(sheet["weight"]) == tip[name]["weight"]
    # Flip preference back to live and reseat — gated rematerialize must still
    # leave durable materials only when the agent left the gate wired.
    (OPS / "prefer.toml").write_text('mode = "live"\ntag_path = "surface"\n')
    broken = _reseat()
    assert broken["seat_ok"] is False
    north = _parse_kv((ETC / "peers.d" / "north.peer").read_text())
    assert north.get("host", "").startswith("10.") or int(north.get("weight", "0")) != 100
    # Restore durable preference and reseat — seat must recover without rewrite.
    (OPS / "prefer.toml").write_text('mode = "durable"\ntag_path = "authority"\n')
    recovered = _reseat()
    assert recovered["seat_ok"] is True
    assert recovered["peers"] == _expected_peers()
