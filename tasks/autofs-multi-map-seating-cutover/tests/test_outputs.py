"""Verifier for autofs multi-map seating cutover."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

OUT = Path("/output/autofs-seat.json")
ROSTER = Path("/etc/autofs/roster.list")
DURABLE_MAPS = Path("/var/lib/autofs/maps")
FLOOR_D = Path("/var/lib/autofs/floors")
HOLD_D = Path("/var/lib/autofs/holds")
CLOCK = Path("/var/lib/autofs/state/clock.epoch")
JOURNAL = Path("/var/lib/autofs/ops/journal.jsonl")
GEN_TARGET = Path("/var/lib/autofs/state/gen.target")
EFF = Path("/etc/autofs/effective.conf")
SITE = Path("/app/config/site_standard.conf")
ABORT_PKG = Path("/var/lib/autofs/ops/abort.d/90-local.conf")
LIVE_90 = Path("/etc/auto.master.d/90-local.conf")
RECEIPT = Path("/var/lib/autofs/state/cutover.ok")


def _run_seat() -> None:
    subprocess.run(["/app/ops/run_autofs_seat.sh"], check=False)


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


def _expected_doc() -> dict:
    tips = _sealed_tips()
    clock = int(CLOCK.read_text().strip())
    site = _load_kv(SITE)
    abort = site.get("abort", "none")

    holds = []
    hold_block: dict[str, bool] = {}
    for hp in sorted(HOLD_D.glob("*.hold")):
        key = hp.stem
        kv = _load_kv(hp)
        until_epoch = int(kv.get("until_epoch", "0"))
        holds.append({"key": key, "until_epoch": until_epoch})
        hold_block[key] = until_epoch <= clock

    maps = []
    for name in _roster():
        tip = int(tips.get(name, 0))
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        elig = tip >= floor
        blocked = hold_block.get(name, False)
        aborted = abort == name
        active = bool(elig and not blocked and not aborted)
        maps.append(
            {
                "name": name,
                "mountpoint": f"/mnt/{name}",
                "generation": tip,
                "source": str(DURABLE_MAPS / f"{name}.map"),
                "active": active,
            }
        )

    return {
        "schema_tag": "autofs-seat-v1",
        "maps": maps,
        "holds": holds,
        "seating_ok": True,
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
    assert OUT.is_file(), "missing /output/autofs-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, and seating_ok."""
    doc = _doc()
    assert doc["schema_tag"] == "autofs-seat-v1"
    assert isinstance(doc["maps"], list) and len(doc["maps"]) == len(_roster())
    assert isinstance(doc["holds"], list)
    assert doc["seating_ok"] is True
    for m in doc["maps"]:
        assert set(m) >= {"name", "mountpoint", "generation", "source", "active"}
        assert isinstance(m["generation"], int)
        assert isinstance(m["active"], bool)
    for h in doc["holds"]:
        assert set(h) >= {"key", "until_epoch"}
        assert isinstance(h["until_epoch"], int)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output."""
    a = Path("/tmp/seat_first.bin").read_bytes()
    b = Path("/tmp/seat_second.bin").read_bytes()
    assert a and b and a == b


def test_w7_quartz() -> None:
    """Frozen fixtures under /app/data/maps remain packaging-pinned."""
    pin = Path("/app/packaging/maps.sha256")
    assert pin.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/maps.sha256"],
        cwd="/app/data/maps",
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


def test_v5_coral() -> None:
    """Generation vs durable floor polarity across the roster."""
    doc = _doc()
    exp = {m["name"]: m for m in _expected_doc()["maps"]}
    for m in doc["maps"]:
        e = exp[m["name"]]
        assert m["generation"] == e["generation"]
        tip = m["generation"]
        floor = int((FLOOR_D / f"{m['name']}.floor").read_text().strip())
        if tip < floor:
            assert m["active"] is False


def test_p9_jade() -> None:
    """Expired hold blocks activity; live hold does not."""
    doc = _doc()
    by_name = {m["name"]: m for m in doc["maps"]}
    clock = int(CLOCK.read_text().strip())
    gamma_until = int(_load_kv(HOLD_D / "gamma.hold")["until_epoch"])
    delta_until = int(_load_kv(HOLD_D / "delta.hold")["until_epoch"])
    assert gamma_until <= clock
    assert delta_until > clock
    assert by_name["gamma"]["active"] is False
    assert by_name["delta"]["active"] is True


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
    by_name = {m["name"]: m for m in doc["maps"]}
    assert by_name["epsilon"]["active"] is True


def test_c1_flint() -> None:
    """Matching cutover.ok receipt; gen.live aligned to target."""
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    target = GEN_TARGET.read_text().strip()
    assert kv.get("gen") == target
    assert kv.get("mode") == "seal"
    live = Path("/var/lib/autofs/state/gen.live").read_text().strip()
    assert live == target


def test_r6_slate() -> None:
    """Every map source is the durable maps path."""
    doc = _doc()
    for m in doc["maps"]:
        want = str(DURABLE_MAPS / f"{m['name']}.map")
        assert m["source"] == want
        assert Path(m["source"]).is_file()
        assert Path(m["source"]).resolve().is_relative_to(DURABLE_MAPS.resolve())


def test_u2_mica() -> None:
    """Holds array matches durable windows; seating_ok stays true."""
    doc = _doc()
    exp = _expected_doc()
    got = sorted(doc["holds"], key=lambda h: h["key"])
    want = sorted(exp["holds"], key=lambda h: h["key"])
    assert got == want
    assert doc["seating_ok"] is True


def test_m1_opal() -> None:
    """Full roster active/inactive matrix against durable authority."""
    doc = _doc()
    exp = {m["name"]: m for m in _expected_doc()["maps"]}
    assert sorted(m["name"] for m in doc["maps"]) == sorted(exp)
    for m in doc["maps"]:
        e = exp[m["name"]]
        assert m["active"] == e["active"], m["name"]
        assert m["generation"] == e["generation"]
        assert m["mountpoint"] == e["mountpoint"]
        assert m["source"] == e["source"]
    by_name = {m["name"]: m for m in doc["maps"]}
    assert by_name["alpha"]["active"] is True
    assert by_name["beta"]["active"] is False
    assert by_name["gamma"]["active"] is False
    assert by_name["delta"]["active"] is True
    assert by_name["epsilon"]["active"] is True


def test_t4_pearl() -> None:
    """Surface autofshealth may print OK; deep seating still required."""
    proc = subprocess.run(
        ["/usr/local/bin/autofshealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "OK" in proc.stdout
    doc = _doc()
    assert doc["seating_ok"] is True
    assert doc["schema_tag"] == "autofs-seat-v1"
