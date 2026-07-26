"""Verifier for the cache-volume mode seating desk."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

SEAT = "/app/ops/run_lvmcache_seat.sh"
SCHEMA = "lvmcache-seat-v1"
OUT = Path("/output/lvmcache-seat.json")
ROSTER = Path("/etc/lvm/roster.list")
DURABLE_VOL = Path("/var/lib/lvm/volumes")
FLOOR_D = Path("/var/lib/lvm/floors")
HOLD_D = Path("/var/lib/lvm/holds")
STATE = Path("/var/lib/lvm/state")
CLOCK = STATE / "clock.epoch"
GEN_TARGET = STATE / "gen.target"
GEN_LIVE = STATE / "gen.live"
OPS = Path("/var/lib/lvm/ops")
JOURNAL = OPS / "journal.jsonl"
POOL_MAP = OPS / "pool.map"
FROZEN_POOL_MAP = Path("/app/data/lvm/pool.map")
PIN = Path("/app/packaging/lvm.sha256")
PREFER = OPS / "prefer.toml"
RECEIPT = OPS / "state" / "apply.ok"
SURFACE = OPS / "surface.modes"
ABORT_PKG = OPS / "abort.d" / "90-local.conf"
SHEET_D = Path("/etc/lvm/cache.d")
DROPIN_D = Path("/etc/lvm/lvm.conf.d")
LIVE_90 = DROPIN_D / "90-local.conf"
EFF = Path("/etc/lvm/effective.conf")
SITE = Path("/app/config/site_standard.conf")


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
    """The cutover row whose generation equals the target and whose mode is sealed."""
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


def _surface_modes() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in SURFACE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = dict(
            part.split("=", 1) for part in line.split() if "=" in part
        )
        if "lv" in fields:
            out[fields["lv"]] = fields.get("mode", "")
    return out


def _expected_doc() -> dict:
    row = _sealed_row()
    tips = {k: int(v) for k, v in row.get("tips", {}).items()}
    modes = dict(row.get("modes", {}))
    clock = int(CLOCK.read_text().strip())
    guard = _load_kv(SITE).get("abort", "none")
    sealed_pool = _load_kv(POOL_MAP)

    holds = []
    shut: dict[str, bool] = {}
    for hp in sorted(HOLD_D.glob("*.hold")):
        until_epoch = int(_load_kv(hp).get("until_epoch", "0"))
        holds.append({"lv": hp.stem, "until_epoch": until_epoch})
        shut[hp.stem] = until_epoch > clock

    volumes = []
    for name in _roster():
        tip = int(tips.get(name, 0))
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        attached = bool(
            tip >= floor and not shut.get(name, False) and guard != name
        )
        volumes.append(
            {
                "name": name,
                "vg": _load_kv(DURABLE_VOL / f"{name}.toml").get("vg", ""),
                "mode": modes.get(name, ""),
                "cachepool": sealed_pool.get(name, ""),
                "generation": tip,
                "attached": attached,
            }
        )

    return {
        "schema_tag": SCHEMA,
        "volumes": volumes,
        "holds": holds,
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
    assert OUT.is_file(), "missing /output/lvmcache-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, field types, and seat_ok."""
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert isinstance(doc["volumes"], list)
    assert len(doc["volumes"]) == len(_roster())
    assert isinstance(doc["holds"], list)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"], "desk did not settle"
    for v in doc["volumes"]:
        assert set(v) >= {
            "name",
            "vg",
            "mode",
            "cachepool",
            "generation",
            "attached",
        }
        assert isinstance(v["generation"], int)
        assert isinstance(v["attached"], bool)
        assert isinstance(v["vg"], str) and v["vg"]
        assert isinstance(v["mode"], str) and v["mode"]
        assert isinstance(v["cachepool"], str) and v["cachepool"]
    for h in doc["holds"]:
        assert set(h) >= {"lv", "until_epoch"}
        assert isinstance(h["until_epoch"], int)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output."""
    a = Path("/tmp/seat_first.bin").read_bytes()
    b = Path("/tmp/seat_second.bin").read_bytes()
    assert a and b and a == b


def test_w7_quartz() -> None:
    """Frozen fixture tree stays packaging-pinned and the sealed copy matches."""
    assert PIN.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/lvm.sha256"],
        cwd="/app/data/lvm",
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert POOL_MAP.read_text() == FROZEN_POOL_MAP.read_text()


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
            assert not v["attached"], v["name"]
    by_name = {v["name"]: v["attached"] for v in doc["volumes"]}
    assert {n: by_name[n] for n in ("alpha", "beta")} == {
        "alpha": True,
        "beta": False,
    }


def test_p9_jade() -> None:
    """An open maintenance window blocks; an expired one does not."""
    doc = _doc()
    by_name = {v["name"]: v["attached"] for v in doc["volumes"]}
    clock = int(CLOCK.read_text().strip())
    gamma_until = int(_load_kv(HOLD_D / "gamma.hold")["until_epoch"])
    delta_until = int(_load_kv(HOLD_D / "delta.hold")["until_epoch"])
    assert gamma_until > clock
    assert delta_until <= clock
    assert {n: by_name[n] for n in ("gamma", "delta")} == {
        "gamma": False,
        "delta": True,
    }


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
    by_name = {v["name"]: v["attached"] for v in doc["volumes"]}
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
    """Cachepool identity is the sealed one and modes are the durable tips."""
    doc = _doc()
    sealed_pool = _load_kv(POOL_MAP)
    modes = dict(_sealed_row().get("modes", {}))
    for v in doc["volumes"]:
        name = v["name"]
        assert v["cachepool"] == sealed_pool[name], name
        assert v["mode"] == modes[name], name
        sheet = _load_kv(SHEET_D / f"{name}.conf")
        assert sheet.get("pool_uuid") == sealed_pool[name], name
        assert sheet.get("cache_mode") == modes[name], name


def test_u2_mica() -> None:
    """Maintenance windows are reported from the durable window files."""
    doc = _doc()
    exp = _expected_doc()
    got = sorted(doc["holds"], key=lambda h: h["lv"])
    want = sorted(exp["holds"], key=lambda h: h["lv"])
    assert got == want
    assert doc["seat_ok"] == exp["seat_ok"]


def test_m1_opal() -> None:
    """Full roster attach matrix against the durable authority."""
    doc = _doc()
    exp = {v["name"]: v for v in _expected_doc()["volumes"]}
    assert sorted(v["name"] for v in doc["volumes"]) == sorted(exp)
    for v in doc["volumes"]:
        e = exp[v["name"]]
        assert v["attached"] == e["attached"], v["name"]
        assert v["generation"] == e["generation"], v["name"]
        assert v["vg"] == e["vg"], v["name"]
        assert v["mode"] == e["mode"], v["name"]
        assert v["cachepool"] == e["cachepool"], v["name"]
    by_name = {v["name"]: v["attached"] for v in doc["volumes"]}
    assert by_name == {
        "alpha": True,
        "beta": False,
        "gamma": False,
        "delta": True,
        "epsilon": True,
        "zeta": True,
    }


def test_t4_pearl() -> None:
    """Surface probe may print OK while deep seating still has to agree."""
    proc = subprocess.run(
        ["/usr/local/bin/lvmhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "OK" in proc.stdout
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert doc["seat_ok"], "surface probe is green while deep seating is not"


def test_k5_garnet() -> None:
    """Re-entry restores the report and attached rows never carry working-sheet modes."""
    surface = _surface_modes()
    modes = dict(_sealed_row().get("modes", {}))
    OUT.write_text('{"schema_tag": "seat-draft", "seat_ok": true}\n')
    _run_seat()
    doc = _doc()
    assert doc["schema_tag"] == SCHEMA
    assert doc["seat_ok"], "re-entry left the desk unsettled"
    attached = [v for v in doc["volumes"] if v["attached"]]
    assert len(attached) >= 4
    for v in attached:
        assert v["mode"] == modes[v["name"]], v["name"]
    drifted = [v for v in attached if v["mode"] != surface[v["name"]]]
    assert len(drifted) >= 2
    exp = {v["name"]: v["attached"] for v in _expected_doc()["volumes"]}
    assert {v["name"]: v["attached"] for v in doc["volumes"]} == exp
