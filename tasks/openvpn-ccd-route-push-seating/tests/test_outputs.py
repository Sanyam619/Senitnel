"""Verifier for OpenVPN CCD route-push seating.

Re-enters /app/ops/run_ovpn_seat.sh and derives EXPECTED seating from
durable fixtures under /app/data and /var/lib/openvpn — not from agent
output alone.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/ovpn-seat.json")
DATA_OVPN = Path("/app/data/ovpn")
SITE = Path("/app/config/site_standard.conf")
ETC = Path("/etc/openvpn")
VAR = Path("/var/lib/openvpn")
OPS = VAR / "ops"
ROSTER = ETC / "server" / "roster.list"
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
        row["cn"]: {
            "iroute": row["iroute"],
            "generation": int(target),
        }
        for row in chosen["rows"]
    }


def _journal_eligible() -> set[str]:
    target = (VAR / "state" / "gen.target").read_text().strip()
    admitted: set[str] = set()
    revoked: set[str] = set()
    seal_ok = False
    for line in (VAR / "ops" / "clients.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "seal" and str(row.get("gen")) == target:
            seal_ok = True
        if str(row.get("gen")) != target:
            continue
        name = row.get("cn")
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
    for path in sorted((ETC / "server" / "conf.d").glob("*.conf")):
        for raw in path.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line.startswith("abort="):
                continue
            val = line.split("=", 1)[1].strip()
            if val:
                aborts.add(val)
    return aborts


def _durable_iroute(cn: str) -> str:
    fixture = DATA_OVPN / f"{cn}.toml"
    for line in fixture.read_text().splitlines():
        if line.strip().startswith("iroute"):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError(f"missing iroute in {fixture}")


def _floor(cn: str) -> int:
    return int((VAR / "floors" / f"{cn}.floor").read_text().strip())


def _expected_clients() -> list[dict]:
    tip = _prefer_tip()
    eligible = _journal_eligible()
    aborted = _abort_set()
    rows = []
    for cn in _roster():
        t = tip[cn]
        pushed = (
            cn in eligible
            and cn not in aborted
            and t["generation"] >= _floor(cn)
        )
        rows.append(
            {
                "cn": cn,
                "iroute": t["iroute"],
                "generation": t["generation"],
                "pushed": pushed,
            }
        )
    return rows


def _expected_pools() -> list[dict]:
    pools = []
    for raw in (OPS / "pools.toml").read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        name, rest = line.split("=", 1)
        name = name.strip()
        cidr, mark = [p.strip() for p in rest.split(",", 1)]
        active = mark == "prefer"
        pools.append({"name": name, "cidr": cidr, "active": active})
    return pools


def _prefer_mode() -> str:
    text = (OPS / "prefer.toml").read_text()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("mode"):
            return line.split("=", 1)[1].strip().strip('"')
    return "live"


def _ccd_iroute(cn: str) -> str:
    path = ETC / "ccd" / cn
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("iroute "):
            return line.split(None, 1)[1].strip()
    return ""


def _reseat() -> dict:
    REPORT.unlink(missing_ok=True)
    proc = subprocess.run(
        ["/bin/bash", "/app/ops/run_ovpn_seat.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/ovpn-seat.json"
    return json.loads(REPORT.read_text())


def test_q3_topaz():
    """Ledger schema, schema_tag, seat_ok, and pushed polarity after seating."""
    doc = _reseat()
    assert doc["schema_tag"] == "ovpn-seat-v1"
    assert isinstance(doc["clients"], list)
    assert isinstance(doc["pools"], list)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"] is True
    needed = {"cn", "iroute", "generation", "pushed"}
    for row in doc["clients"]:
        assert needed <= set(row)
        assert isinstance(row["generation"], int)
        assert isinstance(row["pushed"], bool)
        assert "/" in row["iroute"]
    for row in doc["pools"]:
        assert {"name", "cidr", "active"} <= set(row)
        assert isinstance(row["active"], bool)
    by_cn = {c["cn"]: c for c in doc["clients"]}
    assert by_cn["flint"]["pushed"] is True
    assert by_cn["beryl"]["pushed"] is True
    assert by_cn["mica"]["pushed"] is True
    assert by_cn["quartz"]["pushed"] is False
    assert by_cn["jasper"]["pushed"] is False
    assert by_cn["onyx"]["pushed"] is False
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
    """Tip iroute state records match prefer journal and report."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    by_cn = {c["cn"]: c for c in doc["clients"]}
    tip = _prefer_tip()
    for cn in _roster():
        fixture = DATA_OVPN / f"{cn}.toml"
        assert fixture.is_file(), cn
        text = fixture.read_text()
        assert f'name = "{cn}"' in text
        tip_iroute = (VAR / "state" / f"tip_{cn}.iroute").read_text().strip()
        tip_gen = int((VAR / "state" / f"tip_{cn}.gen").read_text().strip())
        assert tip_iroute == tip[cn]["iroute"]
        assert tip_gen == tip[cn]["generation"]
        assert by_cn[cn]["iroute"] == tip_iroute
        assert tip_iroute == _durable_iroute(cn)


def test_v5_coral():
    """Sealed complete prefer tip beats incomplete later tip iroutes."""
    doc = _reseat()
    by_cn = {c["cn"]: c for c in doc["clients"]}
    assert by_cn["beryl"]["iroute"] == "10.8.5.0/24"
    assert by_cn["beryl"]["iroute"] != "10.8.99.0/24"
    assert by_cn["beryl"]["iroute"] != "10.8.51.0/24"
    assert by_cn["flint"]["iroute"] == "10.8.1.0/24"
    assert by_cn["flint"]["iroute"] != "10.8.50.0/24"


def test_p9_jade():
    """Revoked journal client is never pushed."""
    doc = _reseat()
    by_cn = {c["cn"]: c for c in doc["clients"]}
    assert by_cn["jasper"]["pushed"] is False
    assert "jasper" not in _journal_eligible()


def test_h8_amber():
    """Abort package stays forensic while live drop-in is site-standard."""
    _reseat()
    abort_kv = _parse_kv((VAR / "ops" / "abort.d" / "90-local.conf").read_text())
    live_kv = _parse_kv((ETC / "server" / "conf.d" / "90-local.conf").read_text())
    site_kv = _parse_kv(SITE.read_text())
    assert abort_kv.get("pool_policy") == "prefer_abort"
    assert abort_kv.get("abort") == "onyx"
    assert live_kv.get("pool_policy") == "prefer_ccd"
    assert live_kv.get("pool_policy") == site_kv["pool_policy"]
    assert live_kv.get("bind_order") == site_kv["bind_order"]
    for key, val in site_kv.items():
        if key.startswith("pool."):
            assert live_kv.get(key) == val
    assert live_kv != abort_kv
    assert live_kv.get("pool.edge") == "skip"


def test_c1_flint():
    """Stale cutover receipt rematerializes abort then site-standard wins."""
    _reseat()
    receipt = VAR / "state" / "cutover.ok"
    assert receipt.is_file()
    rkv = _parse_kv(receipt.read_text())
    target = (VAR / "state" / "gen.target").read_text().strip()
    assert rkv.get("gen") == target
    assert rkv.get("mode") == "seal"
    live = ETC / "server" / "conf.d" / "90-local.conf"
    assert live.is_file()
    assert live.read_text().strip()
    receipt.write_text("gen=3\nmode=live\n")
    _reseat()
    live_after = _parse_kv(live.read_text())
    assert (VAR / "ops" / "abort.d" / "90-local.conf").is_file()
    assert live_after.get("pool_policy") == "prefer_ccd"
    assert live.is_file()


def test_r6_slate():
    """Abort set excludes onyx; flint and beryl remain pushed."""
    doc = _reseat()
    by_cn = {c["cn"]: c for c in doc["clients"]}
    assert "onyx" in _abort_set()
    assert by_cn["onyx"]["pushed"] is False
    assert by_cn["flint"]["pushed"] is True
    assert by_cn["beryl"]["pushed"] is True


def test_j2_onyx():
    """Prefer-selected pool is active; overlapping decoy stays inactive."""
    doc = _reseat()
    pools = {p["name"]: p for p in doc["pools"]}
    assert pools["core"]["active"] is True
    assert pools["core"]["cidr"] == "10.8.0.0/16"
    assert pools["edge"]["active"] is False
    assert pools["edge"]["cidr"] == "10.8.0.0/16"
    assert pools["lab"]["active"] is False
    assert doc["pools"] == _expected_pools()


def test_m1_opal():
    """Full roster matrix matches durable tip × journal × floor × abort."""
    doc = _reseat()
    assert doc["clients"] == _expected_clients()
    assert doc["pools"] == _expected_pools()
    assert doc["seat_ok"] is True


def test_u2_mica():
    """Quartz sits below durable floor; tip must not push it."""
    doc = _reseat()
    by_cn = {c["cn"]: c for c in doc["clients"]}
    assert by_cn["quartz"]["generation"] == 8
    assert _floor("quartz") == 9
    assert by_cn["quartz"]["pushed"] is False
    assert by_cn["quartz"]["iroute"] == "10.8.2.0/24"
    assert by_cn["mica"]["generation"] == 8
    assert _floor("mica") == 8
    assert by_cn["mica"]["pushed"] is True


def test_k5_garnet():
    """Live CCD sheets carry durable tip iroutes (not surface bait)."""
    doc = _reseat()
    for row in doc["clients"]:
        sheet = _ccd_iroute(row["cn"])
        assert sheet == row["iroute"]
        assert sheet == _durable_iroute(row["cn"])
        assert not sheet.startswith("10.70.")
        if row["cn"] == "beryl":
            assert sheet == "10.8.5.0/24"
            assert sheet != "10.8.99.0/24"


def test_t4_pearl():
    """Surface ovpnhealth connected is not sufficient without durable seat."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    assert doc["clients"] == _expected_clients()
    proc = subprocess.run(
        ["/usr/local/bin/ovpnhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "connected" in proc.stdout.lower()


def test_s8_zircon():
    """Clearing the push ledger and reseating reconstitutes the same matrix."""
    _reseat()
    REPORT.unlink(missing_ok=True)
    (VAR / "state" / "pushed.set").write_text("")
    doc = _reseat()
    assert doc["clients"] == _expected_clients()
    assert doc["seat_ok"] is True


def test_y3_jasper():
    """Preference must be durable/authority and survive stock re-entry."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    assert _prefer_mode() in ALLOWED_PREF
    tip = _prefer_tip()
    for cn in _roster():
        assert (VAR / "state" / f"tip_{cn}.iroute").read_text().strip() == tip[cn]["iroute"]
        assert _ccd_iroute(cn) == _durable_iroute(cn)
    (OPS / "prefer.toml").write_text('mode = "live"\ntag_path = "surface"\n')
    broken = _reseat()
    assert broken["seat_ok"] is False
    flint = _ccd_iroute("flint")
    assert flint.startswith("10.70.") or flint != "10.8.1.0/24"
    (OPS / "prefer.toml").write_text('mode = "durable"\ntag_path = "authority"\n')
    recovered = _reseat()
    assert recovered["seat_ok"] is True
    assert recovered["clients"] == _expected_clients()
    assert recovered["pools"] == _expected_pools()
