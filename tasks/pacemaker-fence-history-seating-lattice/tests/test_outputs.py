"""Verifier for pacemaker fence-history seating lattice."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

OUT = Path("/output/crm-seat.json")
NODE_ROSTER = Path("/var/lib/pacemaker/nodes.roster")
RES_ROSTER = Path("/var/lib/pacemaker/resources.roster")
FLOOR_D = Path("/var/lib/pacemaker/floors")
RES_D = Path("/var/lib/pacemaker/resources")
PREFER = Path("/var/lib/cluster/ops/prefer_journal.jsonl")
FENCE_J = Path("/var/lib/cluster/ops/fence_journal.jsonl")
GEN_TARGET = Path("/var/lib/cluster/ops/state/gen.target")
GEN_LIVE = Path("/var/lib/cluster/ops/state/gen.live")
EFF = Path("/etc/pacemaker/effective.conf")
SITE = Path("/app/config/site_standard.conf")
ABORT_PKG = Path("/var/lib/cluster/ops/abort.d/90-local.conf")
LIVE_90 = Path("/etc/pacemaker/cib.d/90-local.conf")
RECEIPT = Path("/var/lib/cluster/ops/state/cutover.ok")
CLUSTER_DATA = Path("/app/data/cluster")


def _run_seat() -> None:
    subprocess.run(["/app/ops/run_crm_seat.sh"], check=False)


def _load_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _names(path: Path) -> list[str]:
    return [
        ln.strip()
        for ln in path.read_text().splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def _sealed_tips() -> dict[str, int]:
    target = int(GEN_TARGET.read_text().strip())
    tips: dict[str, int] = {}
    for line in PREFER.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if (
            row.get("kind") == "cutover"
            and int(row.get("gen", -1)) == target
            and row.get("mode") == "seal"
        ):
            tips = {k: int(v) for k, v in row.get("tips", {}).items()}
    return tips


def _unretracted() -> dict[str, int]:
    latest: dict[str, tuple[int, str]] = {}
    for line in FENCE_J.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        t = row.get("target")
        if not t:
            continue
        ep = int(row.get("epoch", 0))
        st = str(row.get("status", ""))
        prev = latest.get(t)
        if prev is None or ep >= prev[0]:
            latest[t] = (ep, st)
    return {t: ep for t, (ep, st) in latest.items() if st == "fenced"}


def _expected_doc() -> dict:
    tips = _sealed_tips()
    unretract = _unretracted()
    site = _load_kv(SITE)
    stick = int(site["default_stickiness"])

    nodes = []
    online_map: dict[str, bool] = {}
    for name in _names(NODE_ROSTER):
        tip = int(tips.get(name, 0))
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        online = tip >= floor
        online_map[name] = online
        nodes.append({"name": name, "online": online, "generation": tip})

    resources = []
    for rid in _names(RES_ROSTER):
        kv = _load_kv(RES_D / f"{rid}.toml")
        home = kv["home"]
        start_epoch = int(kv["start_epoch"])
        role = "Stopped"
        if (
            online_map.get(home, False)
            and (home not in unretract or unretract[home] <= start_epoch)
        ):
            role = "Started"
        resources.append(
            {"id": rid, "node": home, "role": role, "stickiness": stick}
        )

    fences = [
        {"target": t, "epoch": e, "status": "fenced"}
        for t, e in sorted(unretract.items(), key=lambda x: (x[0], x[1]))
    ]

    return {
        "schema_tag": "crm-seat-v1",
        "nodes": nodes,
        "resources": resources,
        "fences": fences,
        "seat_ok": True,
    }


@pytest.fixture(scope="module", autouse=True)
def _seat_twice() -> None:
    if OUT.exists():
        OUT.unlink()
    _run_seat()
    first = OUT.read_bytes() if OUT.exists() else b""
    _run_seat()
    second = OUT.read_bytes() if OUT.exists() else b""
    Path("/tmp/seat_first.bin").write_bytes(first)
    Path("/tmp/seat_second.bin").write_bytes(second)


def _doc() -> dict:
    assert OUT.is_file(), "missing /output/crm-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, and seat_ok."""
    doc = _doc()
    assert doc["schema_tag"] == "crm-seat-v1"
    assert isinstance(doc["nodes"], list) and len(doc["nodes"]) == len(_names(NODE_ROSTER))
    assert isinstance(doc["resources"], list) and len(doc["resources"]) == len(
        _names(RES_ROSTER)
    )
    assert isinstance(doc["fences"], list)
    assert doc["seat_ok"] is True
    for n in doc["nodes"]:
        assert set(n) >= {"name", "online", "generation"}
        assert isinstance(n["online"], bool)
        assert isinstance(n["generation"], int)
    for r in doc["resources"]:
        assert set(r) >= {"id", "node", "role", "stickiness"}
        assert isinstance(r["stickiness"], int)
        assert r["role"] in {"Started", "Stopped"}
    for f in doc["fences"]:
        assert set(f) >= {"target", "epoch", "status"}
        assert isinstance(f["epoch"], int)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output."""
    a = Path("/tmp/seat_first.bin").read_bytes()
    b = Path("/tmp/seat_second.bin").read_bytes()
    assert a and b and a == b


def test_w7_quartz() -> None:
    """Frozen fixtures under /app/data/cluster remain packaging-pinned."""
    pin = Path("/app/packaging/cluster.sha256")
    assert pin.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/cluster.sha256"],
        cwd="/app/data/cluster",
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert CLUSTER_DATA.is_dir()


def test_j2_onyx() -> None:
    """Lexical CIB fold effective stickiness matches site-standard tokens."""
    _run_seat()
    eff = _load_kv(EFF)
    site = _load_kv(SITE)
    for k in ("default_stickiness", "bind_order", "location_policy"):
        assert eff.get(k) == site.get(k), f"{k}: {eff.get(k)} != {site.get(k)}"


def test_v5_coral() -> None:
    """Node generation/online polarity against durable prefer tips and floors."""
    doc = _doc()
    tips = _sealed_tips()
    by_name = {n["name"]: n for n in doc["nodes"]}
    for name in _names(NODE_ROSTER):
        tip = int(tips[name])
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        n = by_name[name]
        assert n["generation"] == tip
        assert n["online"] is (tip >= floor)


def test_p9_jade() -> None:
    """Unretracted fence after start epoch blocks Started on that home node."""
    doc = _doc()
    by_id = {r["id"]: r for r in doc["resources"]}
    unretract = _unretracted()
    assert "node_b" in unretract
    assert unretract["node_b"] == 40
    assert by_id["rs_beta"]["node"] == "node_b"
    assert by_id["rs_beta"]["role"] == "Stopped"
    beta_start = int(_load_kv(RES_D / "rs_beta.toml")["start_epoch"])
    assert unretract["node_b"] > beta_start


def test_h8_amber() -> None:
    """Abort package forensic; live 90-local carries site-standard tokens."""
    assert ABORT_PKG.is_file()
    abort_kv = _load_kv(ABORT_PKG)
    assert abort_kv.get("default_stickiness") == "50"
    assert abort_kv.get("location_policy") == "abort_home"
    assert LIVE_90.is_file()
    live_kv = _load_kv(LIVE_90)
    site = _load_kv(SITE)
    assert live_kv.get("default_stickiness") == site.get("default_stickiness")
    assert live_kv.get("location_policy") == site.get("location_policy")
    assert live_kv.get("bind_order") == site.get("bind_order")


def test_c1_flint() -> None:
    """Matching cutover.ok receipt; gen.live aligned to target."""
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    target = GEN_TARGET.read_text().strip()
    assert kv.get("gen") == target
    assert kv.get("mode") == "seal"
    assert GEN_LIVE.read_text().strip() == target


def test_r6_slate() -> None:
    """Full resource role/stickiness/node matrix against durable authority."""
    doc = _doc()
    exp = {r["id"]: r for r in _expected_doc()["resources"]}
    assert sorted(r["id"] for r in doc["resources"]) == sorted(exp)
    for r in doc["resources"]:
        e = exp[r["id"]]
        assert r["node"] == e["node"]
        assert r["role"] == e["role"], r["id"]
        assert r["stickiness"] == e["stickiness"]
    by_id = {r["id"]: r for r in doc["resources"]}
    assert by_id["rs_alpha"]["role"] == "Started"
    assert by_id["rs_beta"]["role"] == "Stopped"
    assert by_id["rs_gamma"]["role"] == "Started"
    assert by_id["rs_delta"]["role"] == "Started"


def test_u2_mica() -> None:
    """Fences array matches sealed unretract continuity only."""
    doc = _doc()
    exp = _expected_doc()["fences"]
    got = sorted(doc["fences"], key=lambda f: (f["target"], f["epoch"]))
    want = sorted(exp, key=lambda f: (f["target"], f["epoch"]))
    assert got == want
    assert all(f["status"] == "fenced" for f in got)
    # Retracted node_c must not appear
    assert all(f["target"] != "node_c" for f in got)


def test_m1_opal() -> None:
    """Nodes array online/generation matrix against durable prefer authority."""
    doc = _doc()
    exp = {n["name"]: n for n in _expected_doc()["nodes"]}
    assert sorted(n["name"] for n in doc["nodes"]) == sorted(exp)
    for n in doc["nodes"]:
        e = exp[n["name"]]
        assert n["online"] == e["online"]
        assert n["generation"] == e["generation"]
    by_name = {n["name"]: n for n in doc["nodes"]}
    assert by_name["node_a"]["online"] is True
    assert by_name["node_b"]["online"] is True
    assert by_name["node_c"]["online"] is True


def test_k5_garnet() -> None:
    """Retracted fence history does not block later Started on that node."""
    doc = _doc()
    by_id = {r["id"]: r for r in doc["resources"]}
    unretract = _unretracted()
    assert "node_c" not in unretract
    assert by_id["rs_gamma"]["node"] == "node_c"
    assert by_id["rs_gamma"]["role"] == "Started"
    # Same unretracted node_b: rs_delta start_epoch past fence epoch → Started
    assert unretract["node_b"] == 40
    delta_start = int(_load_kv(RES_D / "rs_delta.toml")["start_epoch"])
    assert unretract["node_b"] <= delta_start
    assert by_id["rs_delta"]["role"] == "Started"


def test_s8_zircon() -> None:
    """Wipe /output and re-enter seating still agrees with durable EXPECTED."""
    if OUT.exists():
        OUT.unlink()
    _run_seat()
    doc = _doc()
    exp = _expected_doc()
    assert doc["schema_tag"] == exp["schema_tag"]
    assert doc["seat_ok"] is True
    assert {n["name"]: n for n in doc["nodes"]} == {
        n["name"]: n for n in exp["nodes"]
    }
    assert {r["id"]: r for r in doc["resources"]} == {
        r["id"]: r for r in exp["resources"]
    }
    assert sorted(doc["fences"], key=lambda f: (f["target"], f["epoch"])) == sorted(
        exp["fences"], key=lambda f: (f["target"], f["epoch"])
    )


def test_t4_pearl() -> None:
    """Surface crmhealth may print GREEN; deep seat_ok still required."""
    proc = subprocess.run(
        ["/usr/local/bin/crmhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "GREEN" in proc.stdout
    doc = _doc()
    assert doc["seat_ok"] is True
    assert doc["schema_tag"] == "crm-seat-v1"
