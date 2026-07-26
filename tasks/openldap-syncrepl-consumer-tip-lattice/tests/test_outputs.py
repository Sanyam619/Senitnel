"""Verifier for OpenLDAP syncrepl consumer tip seating."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

OUT = Path("/output/ldap-seat.json")
ROSTER = Path("/etc/ldap/roster.list")
FLOOR_D = Path("/var/lib/ldap/floors")
HOLD_D = Path("/var/lib/ldap/holds")
CLOCK = Path("/var/lib/ldap/state/clock.epoch")
JOURNAL = Path("/var/lib/ldap/ops/csn_journal.jsonl")
GEN_TARGET = Path("/var/lib/ldap/state/gen.target")
EFF = Path("/etc/ldap/effective.conf")
SITE = Path("/app/config/site_standard.conf")
RECEIPT = Path("/var/lib/ldap/ops/prefer.accept")
SLAPD = Path("/etc/ldap/slapd.d/cn=config/olcDatabase=mdb.ldif")
SURFACE = Path("/var/lib/ldap/ops/surface.uri")
TIP_ID = Path("/var/lib/ldap/state/tip_id")


def _run_seat() -> None:
    subprocess.run(["/app/ops/run_ldap_seat.sh"], check=False)


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


def _roster() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for ln in ROSTER.read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split("\t")
        name = parts[0]
        suffix = parts[1] if len(parts) > 1 else f"dc={name},dc=lab"
        rows.append((name, suffix))
    return rows


def _sealed() -> dict:
    target = int(GEN_TARGET.read_text().strip())
    sealed: dict = {}
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if (
            row.get("kind") == "seal"
            and int(row.get("gen", -1)) == target
            and row.get("mode") == "seal"
        ):
            sealed = row
    return sealed


def _expected_doc() -> dict:
    sealed = _sealed()
    tips = sealed.get("tips", {}) or {}
    tip_provider = str(sealed.get("provider", ""))
    clock = int(CLOCK.read_text().strip())
    site = _load_kv(SITE)
    prefer_uri = site.get("providerURI", tip_provider)

    holds = []
    hold_block: dict[str, bool] = {}
    for hp in sorted(HOLD_D.glob("*.hold")):
        key = hp.stem
        kv = _load_kv(hp)
        until_epoch = int(kv.get("until_epoch", "0"))
        suffix = kv.get("suffix", f"dc={key},dc=lab")
        holds.append({"suffix": suffix, "until_epoch": until_epoch})
        hold_block[key] = until_epoch > clock

    consumers = []
    for name, _suffix in _roster():
        meta = tips.get(name, {})
        tip = int(meta.get("gen", 0))
        csn = str(meta.get("csn", ""))
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        elig = tip >= floor
        blocked = hold_block.get(name, False)
        bound = bool(elig and not blocked and prefer_uri and "surface-decoy" not in prefer_uri)
        consumers.append(
            {
                "name": name,
                "provider": prefer_uri,
                "contextCSN": csn,
                "generation": tip,
                "bound": bound,
            }
        )

    return {
        "schema_tag": "ldap-seat-v1",
        "consumers": consumers,
        "holds": holds,
        "sync_ok": True,
    }


@pytest.fixture(scope="module", autouse=True)
def _seat_twice() -> None:
    if OUT.exists():
        OUT.unlink()
    _run_seat()
    first = OUT.read_bytes() if OUT.exists() else b""
    _run_seat()
    second = OUT.read_bytes() if OUT.exists() else b""
    Path("/var/lib/ldap/state/seat_pass_a.bin").write_bytes(first)
    Path("/var/lib/ldap/state/seat_pass_b.bin").write_bytes(second)


def _doc() -> dict:
    assert OUT.is_file(), "missing /output/ldap-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, and sync_ok."""
    doc = _doc()
    assert doc["schema_tag"] == "ldap-seat-v1"
    assert isinstance(doc["consumers"], list) and len(doc["consumers"]) == len(_roster())
    assert isinstance(doc["holds"], list)
    assert doc["sync_ok"] is True
    for c in doc["consumers"]:
        assert set(c) >= {"name", "provider", "contextCSN", "generation", "bound"}
        assert isinstance(c["generation"], int)
        assert isinstance(c["bound"], bool)
    for h in doc["holds"]:
        assert set(h) >= {"suffix", "until_epoch"}
        assert isinstance(h["until_epoch"], int)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output."""
    a = Path("/var/lib/ldap/state/seat_pass_a.bin").read_bytes()
    b = Path("/var/lib/ldap/state/seat_pass_b.bin").read_bytes()
    assert a and b and a == b


def test_w7_quartz() -> None:
    """Frozen LDIF samples under /app/data/ldap remain packaging-pinned."""
    pin = Path("/app/packaging/ldap.sha256")
    assert pin.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/ldap.sha256"],
        cwd="/app/data/ldap",
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_j2_onyx() -> None:
    """Lexical prefer fold selects site-standard provider URI."""
    _run_seat()
    eff = _load_kv(EFF)
    site = _load_kv(SITE)
    assert eff.get("providerURI") == site.get("providerURI")
    assert "surface-decoy" not in (eff.get("providerURI") or "")
    doc = _doc()
    for c in doc["consumers"]:
        assert c["provider"] == site.get("providerURI")


def test_v5_coral() -> None:
    """Generation vs durable floor polarity across the roster."""
    doc = _doc()
    exp = {c["name"]: c for c in _expected_doc()["consumers"]}
    for c in doc["consumers"]:
        e = exp[c["name"]]
        assert c["generation"] == e["generation"]
        tip = c["generation"]
        floor = int((FLOOR_D / f"{c['name']}.floor").read_text().strip())
        if tip < floor:
            assert c["bound"] is False


def test_p9_jade() -> None:
    """Active hold blocks binding; expired hold does not."""
    doc = _doc()
    by_name = {c["name"]: c for c in doc["consumers"]}
    clock = int(CLOCK.read_text().strip())
    gamma_until = int(_load_kv(HOLD_D / "gamma.hold")["until_epoch"])
    delta_until = int(_load_kv(HOLD_D / "delta.hold")["until_epoch"])
    assert gamma_until > clock
    assert delta_until <= clock
    assert by_name["gamma"]["bound"] is False
    assert by_name["delta"]["bound"] is True


def test_h8_amber() -> None:
    """Surface URI forensic; live slapd provider not decoy; prefer.accept matches tip."""
    assert SURFACE.is_file()
    assert "surface-decoy" in SURFACE.read_text()
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    assert TIP_ID.is_file()
    assert kv.get("tip") == TIP_ID.read_text().strip()
    slapd = SLAPD.read_text()
    assert "surface-decoy" not in slapd
    assert "provider-a.lab" in slapd
    doc = _doc()
    for c in doc["consumers"]:
        assert "surface-decoy" not in c["provider"]


def test_c1_flint() -> None:
    """prefer.accept tip id aligned; gen.live equals gen.target."""
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    sealed = _sealed()
    assert kv.get("tip") == sealed.get("tip_id")
    live = Path("/var/lib/ldap/state/gen.live").read_text().strip()
    assert live == GEN_TARGET.read_text().strip()


def test_r6_slate() -> None:
    """Every consumer contextCSN equals durable sealed tip."""
    doc = _doc()
    exp = {c["name"]: c for c in _expected_doc()["consumers"]}
    for c in doc["consumers"]:
        assert c["contextCSN"] == exp[c["name"]]["contextCSN"]
        assert "00live" not in c["contextCSN"]


def test_u2_mica() -> None:
    """Holds array matches durable windows; sync_ok stays true."""
    doc = _doc()
    exp = _expected_doc()
    got = sorted(doc["holds"], key=lambda h: h["suffix"])
    want = sorted(exp["holds"], key=lambda h: h["suffix"])
    assert got == want
    assert doc["sync_ok"] is True


def test_m1_opal() -> None:
    """Full roster bound/unbound matrix against durable authority."""
    doc = _doc()
    exp = {c["name"]: c for c in _expected_doc()["consumers"]}
    assert sorted(c["name"] for c in doc["consumers"]) == sorted(exp)
    for c in doc["consumers"]:
        e = exp[c["name"]]
        assert c["bound"] == e["bound"], c["name"]
        assert c["generation"] == e["generation"]
        assert c["provider"] == e["provider"]
        assert c["contextCSN"] == e["contextCSN"]
    by_name = {c["name"]: c for c in doc["consumers"]}
    assert by_name["alpha"]["bound"] is True
    assert by_name["beta"]["bound"] is False
    assert by_name["gamma"]["bound"] is False
    assert by_name["delta"]["bound"] is True
    assert by_name["epsilon"]["bound"] is True


def test_t4_pearl() -> None:
    """Surface ldaphealth may print in-sync; deep seating still required."""
    proc = subprocess.run(
        ["/usr/local/bin/ldaphealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "in-sync" in proc.stdout
    doc = _doc()
    assert doc["sync_ok"] is True
    assert doc["schema_tag"] == "ldap-seat-v1"


def test_k5_garnet() -> None:
    """Novel sealed-journal tip inject shifts contextCSN and generation together."""
    sealed = {
        "kind": "seal",
        "gen": 8,
        "mode": "seal",
        "tip_id": "tip_g8",
        "provider": "ldap://provider-a.lab:389",
        "tips": {
            "alpha": {"csn": "20250701120000.aaaaaaZ#0000f1#000#000000", "gen": 6},
            "beta": {"csn": "20250701120000.bbbbbbZ#0000f2#000#000000", "gen": 2},
            "gamma": {"csn": "20250701120000.ccccccZ#0000f3#000#000000", "gen": 6},
            "delta": {"csn": "20250701120000.ddddddZ#0000f4#000#000000", "gen": 6},
            "epsilon": {"csn": "20250701120000.eeeeeeZ#0000f5#000#000000", "gen": 6},
        },
    }
    with JOURNAL.open("a") as fh:
        fh.write(json.dumps(sealed) + "\n")
    GEN_TARGET.write_text("8\n")
    RECEIPT.write_text("tip=tip_g8\n")
    _run_seat()
    doc = _doc()
    by_name = {c["name"]: c for c in doc["consumers"]}
    assert by_name["alpha"]["contextCSN"] == sealed["tips"]["alpha"]["csn"]
    assert by_name["alpha"]["generation"] == 6
    assert by_name["alpha"]["bound"] is True
    assert by_name["beta"]["generation"] == 2
    assert by_name["beta"]["bound"] is False
    assert by_name["gamma"]["bound"] is False
    assert Path("/var/lib/ldap/state/gen.live").read_text().strip() == "8"
    assert _load_kv(RECEIPT).get("tip") == "tip_g8"
