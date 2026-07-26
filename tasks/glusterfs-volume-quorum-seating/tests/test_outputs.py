"""Verifier for the Gluster volume quorum seating desk."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

SEAT = "/app/ops/run_gluster_seat.sh"
SCHEMA = "gluster-seat-v1"
OUT = Path("/output/gluster-seat.json")
ROSTER = Path("/etc/glusterfs/roster.list")
FLOOR_D = Path("/var/lib/glusterd/floors")
HOLD_D = Path("/var/lib/glusterd/holds")
STATE = Path("/var/lib/glusterd/state")
CLOCK = STATE / "clock.epoch"
GEN_TARGET = STATE / "gen.target"
GEN_LIVE = STATE / "gen.live"
OPS = Path("/var/lib/glusterd/ops")
JOURNAL = OPS / "brick_journal.jsonl"
PIN = Path("/app/packaging/gluster.sha256")
FROZEN = Path("/app/data/gluster")
PREFER = OPS / "prefer.toml"
RECEIPT = OPS / "state" / "apply.ok"
SURFACE = OPS / "surface.bricks"
ABORT_PKG = OPS / "abort.d" / "90-local.conf"
BRICK_D = Path("/etc/glusterfs/bricks.d")
DROPIN_D = Path("/etc/glusterfs/glusterd.d")
LIVE_90 = DROPIN_D / "90-local.conf"
EFF = Path("/etc/glusterfs/effective.conf")
SITE = Path("/app/config/site_standard.conf")
DURABLE_VOL = Path("/var/lib/glusterd/volumes")


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


def _surface_bricks() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for line in SURFACE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = dict(part.split("=", 1) for part in line.split() if "=" in part)
        if "vol" in fields and "bricks" in fields:
            out[fields["vol"]] = [
                p for p in fields["bricks"].split(",") if p
            ]
    return out


def _open_held_bricks() -> set[str]:
    clock = int(CLOCK.read_text().strip())
    held: set[str] = set()
    for hp in HOLD_D.glob("*.hold"):
        kv = _load_kv(hp)
        until = int(kv.get("until_epoch", "0"))
        brick = kv.get("brick", "")
        if until > clock and brick:
            held.add(brick)
    return held


def _expected_doc() -> dict:
    row = _sealed_row()
    tips = {k: int(v) for k, v in row.get("tips", {}).items()}
    bricks = {k: list(v) for k, v in row.get("bricks", {}).items()}
    quorum = {k: int(v) for k, v in row.get("quorum", {}).items()}
    guard = _load_kv(SITE).get("abort", "none")
    held = _open_held_bricks()

    volumes = []
    heals = []
    for name in _roster():
        tip = int(tips.get(name, 0))
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        durable = list(bricks.get(name, []))
        qwant = int(quorum.get(name, 0))
        held_in = [b for b in durable if b in held]
        free = [b for b in durable if b not in held]
        qok = 0 < qwant <= len(free)
        started = bool(
            tip >= floor
            and qok
            and not held_in
            and guard != name
            and tip > 0
        )
        volumes.append(
            {
                "name": name,
                "bricks": durable,
                "quorum": qwant,
                "generation": tip,
                "started": started,
            }
        )
        heals.append({"volume": name, "pending": len(held_in)})

    heals.sort(key=lambda h: h["volume"])
    return {
        "schema_tag": SCHEMA,
        "volumes": volumes,
        "heals": heals,
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
    assert OUT.is_file(), "missing /output/gluster-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, field types, and seat_ok."""
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert isinstance(doc["volumes"], list)
    assert len(doc["volumes"]) == len(_roster())
    assert isinstance(doc["heals"], list)
    assert len(doc["heals"]) == len(_roster())
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"], "desk did not settle"
    for v in doc["volumes"]:
        assert set(v) >= {
            "name",
            "bricks",
            "quorum",
            "generation",
            "started",
        }
        assert isinstance(v["generation"], int)
        assert isinstance(v["quorum"], int)
        assert isinstance(v["started"], bool)
        assert isinstance(v["bricks"], list)
        assert all(isinstance(b, str) and b.startswith("/") for b in v["bricks"])
    for h in doc["heals"]:
        assert set(h) >= {"volume", "pending"}
        assert isinstance(h["pending"], int)
        assert h["pending"] >= 0


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output."""
    assert _SEAT_FIRST and _SEAT_SECOND and _SEAT_FIRST == _SEAT_SECOND


def test_w7_quartz() -> None:
    """Frozen fixture tree stays packaging-pinned and sealed copies match."""
    assert PIN.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/gluster.sha256"],
        cwd="/app/data/gluster",
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for name in _roster():
        frozen = (FROZEN / "volumes" / f"{name}.toml").read_text()
        live = (DURABLE_VOL / f"{name}.toml").read_text()
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
    exp = {v["name"]: v for v in _expected_doc()["volumes"]}
    for v in doc["volumes"]:
        assert v["generation"] == exp[v["name"]]["generation"], v["name"]
        floor = int((FLOOR_D / f"{v['name']}.floor").read_text().strip())
        if v["generation"] < floor:
            assert not v["started"], v["name"]
    by_name = {v["name"]: v["started"] for v in doc["volumes"]}
    assert {n: by_name[n] for n in ("alpha", "beta")} == {
        "alpha": True,
        "beta": False,
    }


def test_p9_jade() -> None:
    """An open brick hold blocks start; an expired hold does not."""
    doc = _doc()
    by_name = {v["name"]: v["started"] for v in doc["volumes"]}
    clock = int(CLOCK.read_text().strip())
    open_holds = []
    expired_holds = []
    for hp in sorted(HOLD_D.glob("*.hold")):
        kv = _load_kv(hp)
        until = int(kv.get("until_epoch", "0"))
        brick = kv.get("brick", "")
        if until > clock:
            open_holds.append((hp.stem, brick, until))
        else:
            expired_holds.append((hp.stem, brick, until))
    assert open_holds, "expected at least one open hold"
    assert expired_holds, "expected at least one expired hold"
    # Open hold belongs to gamma; expired to delta (discoverable from brick path).
    open_vol = open_holds[0][1].strip("/").split("/")[1]
    expired_vol = expired_holds[0][1].strip("/").split("/")[1]
    assert {n: by_name[n] for n in (open_vol, expired_vol)} == {
        open_vol: False,
        expired_vol: True,
    }
    open_row = next(v for v in doc["volumes"] if v["name"] == open_vol)
    assert open_holds[0][1] in open_row["bricks"]
    assert not open_row["started"]


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
    by_name = {v["name"]: v["started"] for v in doc["volumes"]}
    assert {n: by_name[n] for n in ("zeta",)} == {"zeta": True}


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
    """Live brick sheets match the sealed durable sets; quorum from the tip."""
    doc = _doc()
    sealed = _sealed_row()
    bricks = {k: list(v) for k, v in sealed.get("bricks", {}).items()}
    quorum = {k: int(v) for k, v in sealed.get("quorum", {}).items()}
    for v in doc["volumes"]:
        name = v["name"]
        assert sorted(v["bricks"]) == sorted(bricks[name]), name
        assert v["quorum"] == quorum[name], name
        live = [
            ln.strip()
            for ln in (BRICK_D / f"{name}.bricks").read_text().splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        assert sorted(live) == sorted(bricks[name]), name
        assert not any(b.endswith("/b9") for b in live), name


def test_u2_mica() -> None:
    """Heal pending counts open holds on durable bricks; seat_ok settled."""
    doc = _doc()
    exp = _expected_doc()
    got = sorted(doc["heals"], key=lambda h: h["volume"])
    want = sorted(exp["heals"], key=lambda h: h["volume"])
    assert got == want
    assert doc["seat_ok"] == exp["seat_ok"]
    by_vol = {h["volume"]: h["pending"] for h in doc["heals"]}
    assert by_vol["gamma"] == 1
    assert by_vol["delta"] == 0
    assert by_vol["alpha"] == 0


def test_m1_opal() -> None:
    """Full roster started matrix against the durable authority."""
    doc = _doc()
    exp = {v["name"]: v for v in _expected_doc()["volumes"]}
    assert sorted(v["name"] for v in doc["volumes"]) == sorted(exp)
    for v in doc["volumes"]:
        e = exp[v["name"]]
        assert v["started"] == e["started"], v["name"]
        assert v["generation"] == e["generation"], v["name"]
        assert v["quorum"] == e["quorum"], v["name"]
        assert sorted(v["bricks"]) == sorted(e["bricks"]), v["name"]
    by_name = {v["name"]: v["started"] for v in doc["volumes"]}
    assert by_name == {
        "alpha": True,
        "beta": False,
        "gamma": False,
        "delta": True,
        "epsilon": True,
        "zeta": True,
    }


def test_t4_pearl() -> None:
    """Surface probe may print started while deep seating still has to agree."""
    proc = subprocess.run(
        ["/usr/local/bin/glusterhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "started" in proc.stdout.lower()
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert doc["seat_ok"], "surface probe is green while deep seating is not"


def test_k5_garnet() -> None:
    """Re-entry restores the report; started rows never carry surface revoked bricks."""
    surface = _surface_bricks()
    sealed = {k: list(v) for k, v in _sealed_row().get("bricks", {}).items()}
    OUT.write_text('{"schema_tag": "seat-draft", "seat_ok": true}\n')
    _run_seat()
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert doc["seat_ok"], "re-entry left the desk unsettled"
    started = [v for v in doc["volumes"] if v["started"]]
    assert len(started) >= 4
    for v in started:
        assert sorted(v["bricks"]) == sorted(sealed[v["name"]]), v["name"]
        assert not any(b.endswith("/b9") for b in v["bricks"]), v["name"]
    drifted = [
        v
        for v in started
        if sorted(v["bricks"]) != sorted(surface.get(v["name"], []))
    ]
    assert len(drifted) >= 2
    exp = {v["name"]: v["started"] for v in _expected_doc()["volumes"]}
    assert {v["name"]: v["started"] for v in doc["volumes"]} == exp


def test_y3_jasper() -> None:
    """Prefer flip back to surface rematerializes revoked bricks; durable recovers."""
    # Poison: surface plane without receipt must undo durable brick sheets.
    PREFER.write_text('[source]\nplane = "surface"\n')
    if RECEIPT.exists():
        RECEIPT.unlink()
    _run_seat()
    for name in ("alpha", "gamma"):
        live = [
            ln.strip()
            for ln in (BRICK_D / f"{name}.bricks").read_text().splitlines()
            if ln.strip()
        ]
        assert any(b.endswith("/b9") for b in live), name
    # Restore durable authority the way a correct desk does.
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
    sealed = {k: list(v) for k, v in _sealed_row().get("bricks", {}).items()}
    for v in doc["volumes"]:
        assert sorted(v["bricks"]) == sorted(sealed[v["name"]]), v["name"]
        live = [
            ln.strip()
            for ln in (BRICK_D / f"{v['name']}.bricks").read_text().splitlines()
            if ln.strip()
        ]
        assert sorted(live) == sorted(sealed[v["name"]]), v["name"]
    by_vol = {h["volume"]: h["pending"] for h in doc["heals"]}
    assert by_vol["gamma"] == 1
