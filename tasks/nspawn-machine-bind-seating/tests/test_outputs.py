"""Verifier for systemd-nspawn machine bind seating."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

OUT = Path("/output/nspawn-seat.json")
ROSTER = Path("/etc/systemd/nspawn/roster.list")
DURABLE_ROOT = Path("/var/lib/machines/images")
VOL = Path("/var/lib/machines/volumes")
BIND = Path("/var/lib/machines/bind")
FLOOR_D = Path("/var/lib/machines/floors")
JOURNAL = Path("/var/lib/machines/ops/journal.jsonl")
GEN_TARGET = Path("/var/lib/machines/state/gen.target")
EFF = Path("/etc/systemd/nspawn/effective.conf")
SITE = Path("/app/config/site_standard.conf")
ABORT_PKG = Path("/var/lib/machines/ops/abort.d/90-local.conf")
LIVE_90 = Path("/etc/systemd/system/machines.target.wants/90-local.conf")
RECEIPT = Path("/var/lib/machines/state/cutover.ok")
PORTS_DUR = Path("/var/lib/machines/ops/ports.toml")
NSP = Path("/etc/systemd/nspawn")


def _run_seat() -> None:
    subprocess.run(["/app/ops/run_nspawn_seat.sh"], check=False)


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


def _roster() -> list[str]:
    return [
        ln.strip()
        for ln in ROSTER.read_text().splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def _sealed_tips() -> dict[str, int]:
    target = int(GEN_TARGET.read_text().strip())
    tips: dict[str, int] = {}
    for line in JOURNAL.read_text().splitlines():
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


def _same_inode(a: Path, b: Path) -> bool:
    if not a.exists() or not b.exists():
        return False
    sa = os.stat(a)
    sb = os.stat(b)
    return sa.st_ino == sb.st_ino and sa.st_dev == sb.st_dev


def _durable_ports() -> list[dict]:
    ports = []
    for line in PORTS_DUR.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        host, cont = v.split(":", 1)
        ports.append({"machine": k, "host": int(host), "container": int(cont)})
    return ports


def _expected_doc() -> dict:
    tips = _sealed_tips()
    site = _load_kv(SITE)
    abort = site.get("abort", "none")
    machines = []
    for name in _roster():
        tip = int(tips.get(name, 0))
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        elig = tip >= floor
        durable = str(DURABLE_ROOT / name / "root")
        bind = [str(BIND / name / "data")]
        active = bool(elig and abort != name)
        machines.append(
            {
                "name": name,
                "root": durable,
                "bind": bind,
                "generation": tip,
                "active": active,
            }
        )
    return {
        "schema_tag": "nspawn-seat-v1",
        "machines": machines,
        "ports": _durable_ports(),
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
    Path("/var/run/machines/seat_first.bin").write_bytes(first)
    Path("/var/run/machines/seat_second.bin").write_bytes(second)


def _doc() -> dict:
    assert OUT.is_file(), "missing /output/nspawn-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, and seat_ok."""
    doc = _doc()
    assert doc["schema_tag"] == "nspawn-seat-v1"
    assert isinstance(doc["machines"], list) and len(doc["machines"]) == len(_roster())
    assert isinstance(doc["ports"], list) and len(doc["ports"]) == len(_roster())
    assert doc["seat_ok"] is True
    for m in doc["machines"]:
        assert set(m) >= {"name", "root", "bind", "generation", "active"}
        assert isinstance(m["bind"], list)
        assert isinstance(m["generation"], int)
        assert isinstance(m["active"], bool)
    for p in doc["ports"]:
        assert set(p) >= {"machine", "host", "container"}
        assert isinstance(p["host"], int)
        assert isinstance(p["container"], int)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output; wipe-and-reseat still agrees."""
    run_dir = Path("/var/run/machines")
    a = (run_dir / "seat_first.bin").read_bytes()
    b = (run_dir / "seat_second.bin").read_bytes()
    assert a and b and a == b
    if OUT.exists():
        OUT.unlink()
    _run_seat()
    again = OUT.read_bytes()
    assert again == a


def test_w7_quartz() -> None:
    """Frozen fixtures under /app/data/machines remain packaging-pinned."""
    pin = Path("/app/packaging/machines.sha256")
    assert pin.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/machines.sha256"],
        cwd="/app/data/machines",
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_j2_onyx() -> None:
    """Lexical fold effective policy matches site-standard tokens."""
    _run_seat()
    eff = _load_kv(EFF)
    site = _load_kv(SITE)
    for k in ("tip_policy", "bind_order", "abort"):
        assert eff.get(k) == site.get(k), f"{k}: {eff.get(k)} != {site.get(k)}"


def test_r6_slate() -> None:
    """Every machine root is the durable image tip, not the live shadow."""
    doc = _doc()
    for m in doc["machines"]:
        want = str(DURABLE_ROOT / m["name"] / "root")
        assert m["root"] == want
        assert Path(m["root"]).is_file()
        live = Path(f"/var/lib/machines/live/{m['name']}/root")
        assert Path(m["root"]).resolve() != live.resolve()
        unit = NSP / f"{m['name']}.nspawn"
        dirs = [
            ln.split("=", 1)[1]
            for ln in unit.read_text().splitlines()
            if ln.startswith("Directory=")
        ]
        assert dirs == [want]
        assert all("/live/" not in d for d in dirs)


def test_b3_zircon() -> None:
    """Every Bind= path is same-inode attached to the sealed volume object."""
    _run_seat()
    doc = _doc()
    for m in doc["machines"]:
        sealed = VOL / m["name"] / "data"
        assert sealed.is_file()
        assert m["bind"], m["name"]
        for bp in m["bind"]:
            p = Path(bp)
            assert p.is_file(), bp
            assert _same_inode(p, sealed), f"{bp} not same inode as {sealed}"
            # String-equal copies must not satisfy: content match alone is insufficient
            # (already enforced by inode check above).


def test_v5_coral() -> None:
    """Generation vs durable floor polarity across the roster."""
    doc = _doc()
    exp = {m["name"]: m for m in _expected_doc()["machines"]}
    for m in doc["machines"]:
        e = exp[m["name"]]
        assert m["generation"] == e["generation"]
        tip = m["generation"]
        floor = int((FLOOR_D / f"{m['name']}.floor").read_text().strip())
        if tip < floor:
            assert m["active"] is False
            assert m["name"] == "delta"


def test_h8_amber() -> None:
    """Abort package forensic; live 90-local site-standard; epsilon active when abort=none."""
    assert ABORT_PKG.is_file()
    abort_kv = _load_kv(ABORT_PKG)
    assert abort_kv.get("abort") == "epsilon"
    assert abort_kv.get("tip_policy") == "prefer_live"
    assert LIVE_90.is_file()
    live_kv = _load_kv(LIVE_90)
    site = _load_kv(SITE)
    assert live_kv.get("abort") == site.get("abort")
    assert live_kv.get("tip_policy") == site.get("tip_policy")
    doc = _doc()
    by_name = {m["name"]: m for m in doc["machines"]}
    assert by_name["epsilon"]["active"] is True


def test_c1_flint() -> None:
    """Matching cutover.ok receipt; gen.live aligned to target."""
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    target = GEN_TARGET.read_text().strip()
    assert kv.get("gen") == target
    assert kv.get("mode") == "seal"
    live = Path("/var/lib/machines/state/gen.live").read_text().strip()
    assert live == target


def test_p8_garnet() -> None:
    """Ports ledger matches durable ops ports, not the live decoy sheet."""
    doc = _doc()
    got = sorted(doc["ports"], key=lambda p: p["machine"])
    want = sorted(_durable_ports(), key=lambda p: p["machine"])
    assert got == want
    for p in got:
        assert 22000 <= p["host"] <= 22099
        assert p["container"] == 22


def test_u2_mica() -> None:
    """seat_ok stays true; under-floor delta inactive while peers active."""
    doc = _doc()
    assert doc["seat_ok"] is True
    by_name = {m["name"]: m for m in doc["machines"]}
    assert by_name["delta"]["active"] is False
    assert by_name["delta"]["generation"] == 3
    assert by_name["alpha"]["active"] is True
    assert by_name["beta"]["active"] is True
    assert by_name["gamma"]["active"] is True
    assert by_name["epsilon"]["active"] is True


def test_m1_opal() -> None:
    """Full roster active/root/generation matrix against durable authority."""
    doc = _doc()
    exp = {m["name"]: m for m in _expected_doc()["machines"]}
    assert sorted(m["name"] for m in doc["machines"]) == sorted(exp)
    for m in doc["machines"]:
        e = exp[m["name"]]
        assert m["active"] == e["active"], m["name"]
        assert m["generation"] == e["generation"]
        assert m["root"] == e["root"]
        assert m["bind"] == e["bind"]


def test_t4_pearl() -> None:
    """Surface machinectl-health may report OK; deep seating still required."""
    proc = subprocess.run(
        ["/usr/local/bin/machinectl-health"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "OK" in proc.stdout
    doc = _doc()
    assert doc["seat_ok"] is True
    assert doc["schema_tag"] == "nspawn-seat-v1"
