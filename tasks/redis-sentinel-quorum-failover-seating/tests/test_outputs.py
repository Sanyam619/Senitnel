"""Verifier for the Redis Sentinel quorum failover seating desk."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

SEAT = "/app/ops/run_sentinel_seat.sh"
SCHEMA = "sentinel-seat-v1"
OUT = Path("/output/sentinel-seat.json")
ROSTER = Path("/etc/redis/roster.list")
REPLICA_LIST = Path("/etc/redis/replica.list")
FLOOR_D = Path("/var/lib/redis/floors")
STATE = Path("/var/lib/redis/state")
GEN_TARGET = STATE / "gen.target"
GEN_LIVE = STATE / "gen.live"
OPS = Path("/var/lib/redis/ops")
JOURNAL = OPS / "failover_journal.jsonl"
PIN = Path("/app/packaging/redis.sha256")
FROZEN = Path("/app/data/redis")
PREFER = OPS / "prefer.toml"
RECEIPT = OPS / "state" / "apply.ok"
SURFACE = OPS / "surface.monitors"
ABORT_PKG = OPS / "abort.d" / "90-local.conf"
MONITOR_D = Path("/etc/redis/monitors.d")
DROPIN_D = Path("/etc/redis/sentinel.d")
LIVE_90 = DROPIN_D / "90-local.conf"
EFF = Path("/etc/redis/effective.conf")
SITE = Path("/app/config/site_standard.conf")
DURABLE_MASTERS = Path("/var/lib/redis/masters")


def _run_seat() -> None:
    subprocess.run([SEAT], check=False)


def _load_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"')
    return out


def _roster() -> list[str]:
    return [
        ln.strip()
        for ln in ROSTER.read_text().splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def _sealed_row() -> dict:
    target = int(GEN_TARGET.read_text().strip())
    row: dict = {}
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        cand = json.loads(line)
        if (
            cand.get("kind") == "cutover"
            and int(cand.get("gen", -1)) == target
            and cand.get("mode") == "seal"
        ):
            row = cand
    return row


def _surface_monitors() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in SURFACE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _live_monitor_addr(name: str) -> str:
    conf = MONITOR_D / f"{name}.conf"
    if not conf.exists():
        return ""
    for line in conf.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "sentinel" and parts[1] == "monitor":
            return f"{parts[3]}:6379"
    return ""


def _expected_doc() -> dict:
    row = _sealed_row()
    tips = row.get("tips", {})
    qwant = int(row.get("quorum", 0))
    online = list(row.get("sentinels_online", []))
    qok = 0 < qwant <= len(online)
    guard = _load_kv(SITE).get("abort", "none")

    masters = []
    for name in _roster():
        tip = tips.get(name, {})
        addr = tip.get("addr", "")
        gen = int(tip.get("generation", 0))
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        auth = bool(gen >= floor and gen > 0 and qok and guard != name and addr)
        masters.append(
            {
                "name": name,
                "addr": addr,
                "generation": gen,
                "authoritative": auth,
            }
        )

    replicas = []
    for line in REPLICA_LIST.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "|" not in line:
            continue
        m, addr, reported, lag_s = line.split("|", 3)
        tip_addr = tips.get(m, {}).get("addr", "")
        replicas.append(
            {
                "master": m,
                "addr": addr,
                "lag": int(lag_s),
                "attached": reported == tip_addr,
            }
        )

    return {
        "schema_tag": SCHEMA,
        "masters": masters,
        "replicas": replicas,
        "seat_ok": True,
    }


@pytest.fixture(scope="module", autouse=True)
def _seat_twice() -> None:
    global _SEAT_FIRST, _SEAT_SECOND
    if OUT.exists():
        OUT.unlink()
    _run_seat()
    _SEAT_FIRST = OUT.read_bytes() if OUT.exists() else b""
    _run_seat()
    _SEAT_SECOND = OUT.read_bytes() if OUT.exists() else b""


_SEAT_FIRST = b""
_SEAT_SECOND = b""


def _doc() -> dict:
    assert OUT.is_file(), "missing /output/sentinel-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, field types, and seat_ok."""
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert isinstance(doc["masters"], list)
    assert len(doc["masters"]) == len(_roster())
    assert isinstance(doc["replicas"], list)
    assert len(doc["replicas"]) >= 6
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"], "desk did not settle"
    for m in doc["masters"]:
        assert set(m) >= {"name", "addr", "generation", "authoritative"}
        assert isinstance(m["generation"], int)
        assert isinstance(m["authoritative"], bool)
        assert isinstance(m["addr"], str) and ":" in m["addr"]
    for r in doc["replicas"]:
        assert set(r) >= {"master", "addr", "lag", "attached"}
        assert isinstance(r["lag"], int)
        assert isinstance(r["attached"], bool)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output."""
    assert _SEAT_FIRST and _SEAT_SECOND and _SEAT_FIRST == _SEAT_SECOND


def test_w7_quartz() -> None:
    """Frozen fixture tree stays packaging-pinned and sealed copies match."""
    assert PIN.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/redis.sha256"],
        cwd="/app/data/redis",
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for name in _roster():
        frozen = (FROZEN / "masters" / f"{name}.toml").read_text()
        live = (DURABLE_MASTERS / f"{name}.toml").read_text()
        assert frozen == live, name


def test_j2_onyx() -> None:
    """Folded effective policy carries the site-standard tokens."""
    _run_seat()
    eff = _load_kv(EFF)
    site = _load_kv(SITE)
    for k in ("tip_policy", "bind_order", "abort"):
        assert eff.get(k) == site.get(k), f"{k}: {eff.get(k)} != {site.get(k)}"


def test_v5_coral() -> None:
    """Tip generation against the durable floor across the roster."""
    doc = _doc()
    exp = {m["name"]: m for m in _expected_doc()["masters"]}
    for m in doc["masters"]:
        assert m["generation"] == exp[m["name"]]["generation"], m["name"]
        floor = int((FLOOR_D / f"{m['name']}.floor").read_text().strip())
        if m["generation"] < floor:
            assert not m["authoritative"], m["name"]
    by_name = {m["name"]: m["authoritative"] for m in doc["masters"]}
    assert {n: by_name[n] for n in ("alpha", "beta", "epsilon")} == {
        "alpha": True,
        "beta": False,
        "epsilon": False,
    }


def test_p9_jade() -> None:
    """Replicas still reporting a superseded master addr are not attached."""
    doc = _doc()
    superseded = [
        r for r in doc["replicas"] if r["master"] in ("alpha", "gamma") and not r["attached"]
    ]
    attached_ok = [
        r for r in doc["replicas"] if r["master"] in ("alpha", "gamma") and r["attached"]
    ]
    assert len(superseded) == 2
    assert len(attached_ok) == 2
    addrs = {r["addr"] for r in superseded}
    assert "10.20.1.13:6379" in addrs
    assert "10.20.1.33:6379" in addrs
    lags = {r["addr"]: r["lag"] for r in doc["replicas"]}
    assert lags["10.20.1.33:6379"] == 40
    assert lags["10.20.1.13:6379"] == 2


def test_h8_amber() -> None:
    """Abort package stays forensic; live drop-in carries site-standard tokens."""
    assert ABORT_PKG.is_file()
    pkg = _load_kv(ABORT_PKG)
    site = _load_kv(SITE)
    assert pkg.get("abort") == "zeta"
    assert pkg.get("tip_policy") == "prefer_live"
    assert LIVE_90.is_file()
    live = _load_kv(LIVE_90)
    assert live.get("abort") == site.get("abort")
    assert live.get("tip_policy") == site.get("tip_policy")
    assert live.get("bind_order") == site.get("bind_order")
    doc = _doc()
    by_name = {m["name"]: m["authoritative"] for m in doc["masters"]}
    assert by_name["zeta"] is True


def test_c1_flint() -> None:
    """Durable material plane plus a matching apply receipt."""
    assert PREFER.is_file()
    assert _load_kv(PREFER).get("plane") == "durable"
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    target = GEN_TARGET.read_text().strip()
    assert kv.get("gen") == target
    assert kv.get("mode") == "seal"
    assert GEN_LIVE.read_text().strip() == target


def test_r6_slate() -> None:
    """Live monitor lines match sealed durable tip addrs; no surface decoy hosts."""
    doc = _doc()
    sealed = _sealed_row()
    tips = {k: v["addr"] for k, v in sealed.get("tips", {}).items()}
    for m in doc["masters"]:
        name = m["name"]
        assert m["addr"] == tips[name], name
        assert _live_monitor_addr(name) == tips[name], name
        assert _live_monitor_addr(name) != _surface_monitors()[name], name


def test_u2_mica() -> None:
    """Replica attach/lag matrix against durable tip addrs; seat_ok settled."""
    doc = _doc()
    exp = _expected_doc()
    assert doc["replicas"] == exp["replicas"]
    assert doc["seat_ok"] == exp["seat_ok"]
    by_addr = {r["addr"]: r["attached"] for r in doc["replicas"]}
    assert by_addr["10.20.1.12:6379"] is True
    assert by_addr["10.20.1.13:6379"] is False
    assert by_addr["10.20.1.32:6379"] is True
    assert by_addr["10.20.1.33:6379"] is False


def test_m1_opal() -> None:
    """Full roster authoritative matrix against the durable authority."""
    doc = _doc()
    exp = {m["name"]: m for m in _expected_doc()["masters"]}
    assert sorted(m["name"] for m in doc["masters"]) == sorted(exp)
    for m in doc["masters"]:
        e = exp[m["name"]]
        assert m["authoritative"] == e["authoritative"], m["name"]
        assert m["generation"] == e["generation"], m["name"]
        assert m["addr"] == e["addr"], m["name"]
    by_name = {m["name"]: m["authoritative"] for m in doc["masters"]}
    assert by_name == {
        "alpha": True,
        "beta": False,
        "gamma": True,
        "delta": True,
        "epsilon": False,
        "zeta": True,
    }


def test_t4_pearl() -> None:
    """Surface probe may print MASTER-OK while deep seating still has to agree."""
    proc = subprocess.run(
        ["/usr/local/bin/redishhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "MASTER-OK" in proc.stdout
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert doc["seat_ok"], "surface probe is green while deep seating is not"


def test_k5_garnet() -> None:
    """Re-entry restores the report; started monitors never carry surface decoy hosts."""
    surface = _surface_monitors()
    sealed = {k: v["addr"] for k, v in _sealed_row().get("tips", {}).items()}
    OUT.write_text('{"schema_tag": "seat-draft", "seat_ok": true}\n')
    _run_seat()
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert doc["seat_ok"], "re-entry left the desk unsettled"
    auth = [m for m in doc["masters"] if m["authoritative"]]
    assert len(auth) >= 3
    for m in doc["masters"]:
        assert m["addr"] == sealed[m["name"]], m["name"]
        assert _live_monitor_addr(m["name"]) != surface[m["name"]], m["name"]
    exp = {m["name"]: m["authoritative"] for m in _expected_doc()["masters"]}
    assert {m["name"]: m["authoritative"] for m in doc["masters"]} == exp


def test_y3_jasper() -> None:
    """Prefer flip back to surface rematerializes decoy monitors; durable recovers."""
    PREFER.write_text('[source]\nplane = "surface"\n')
    if RECEIPT.exists():
        RECEIPT.unlink()
    _run_seat()
    for name in ("alpha", "gamma"):
        assert _live_monitor_addr(name) == _surface_monitors()[name], name
    target = GEN_TARGET.read_text().strip()
    PREFER.write_text('[source]\nplane = "durable"\n')
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(f"gen={target}\nmode=seal\n")
    LIVE_90.write_text(
        "tip_policy=durable_authority\nbind_order=lexical\nabort=none\n"
    )
    _run_seat()
    doc = _doc()
    assert doc["seat_ok"]
    sealed = {k: v["addr"] for k, v in _sealed_row().get("tips", {}).items()}
    for m in doc["masters"]:
        assert m["addr"] == sealed[m["name"]], m["name"]
        assert _live_monitor_addr(m["name"]) == sealed[m["name"]], m["name"]
    by_addr = {r["addr"]: r["attached"] for r in doc["replicas"]}
    assert by_addr["10.20.1.13:6379"] is False
    assert by_addr["10.20.1.33:6379"] is False
