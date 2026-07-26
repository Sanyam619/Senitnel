"""Verifier for FreeIPA client enrollment tip seating."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

OUT = Path("/output/ipa-seat.json")
HOSTS = Path("/etc/ipa/hosts.list")
SERVICES = Path("/etc/ipa/services.list")
FLOOR_D = Path("/var/lib/ipa/floors")
DOM_D = Path("/etc/sssd/conf.d")
CLOCK = Path("/var/lib/ipa/state/clock.epoch")
JOURNAL = Path("/var/lib/ipa/ops/enroll_journal.jsonl")
GEN_TARGET = Path("/var/lib/ipa/state/gen.target")
EFF = Path("/etc/ipa/effective.conf")
SITE = Path("/app/config/site_standard.conf")
RECEIPT = Path("/var/lib/ipa/ops/prefer.accept")
SSSD = Path("/etc/sssd/sssd.conf")
SURFACE = Path("/var/lib/ipa/ops/surface.realm")
TIP_ID = Path("/var/lib/ipa/state/tip_id")


def _run_seat() -> None:
    subprocess.run(["/app/ops/run_ipa_seat.sh"], check=False)


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


def _hosts() -> list[str]:
    rows: list[str] = []
    for ln in HOSTS.read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        rows.append(ln.split("\t")[0])
    return rows


def _services() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for ln in SERVICES.read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split("\t")
        rows.append((parts[0], parts[1] if len(parts) > 1 else ""))
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


def _abort_until() -> dict[str, int]:
    out: dict[str, int] = {}
    for cp in sorted(DOM_D.glob("*.conf")):
        kv = _load_kv(cp)
        host = kv.get("host", cp.stem)
        out[host] = int(kv.get("abort_until", "0"))
    return out


def _expected_doc() -> dict:
    sealed = _sealed()
    tips = sealed.get("tips", {}) or {}
    clock = int(CLOCK.read_text().strip())
    prefer_realm = _load_kv(SITE).get("realm", "")
    realm_ok = bool(prefer_realm) and "SURFACE-DECOY" not in prefer_realm
    abort = _abort_until()

    enrolled: dict[str, bool] = {}
    host_rows = []
    for name in _hosts():
        meta = tips.get(name, {})
        gen = int(meta.get("gen", 0))
        fpr = str(meta.get("fpr", ""))
        floor = int((FLOOR_D / f"{name}.floor").read_text().strip())
        elig = gen >= floor
        blocked = abort.get(name, 0) > clock
        is_enrolled = bool(elig and not blocked and fpr and realm_ok)
        enrolled[name] = is_enrolled
        host_rows.append(
            {
                "name": name,
                "realm": prefer_realm,
                "keytab": fpr,
                "generation": gen,
                "enrolled": is_enrolled,
            }
        )

    svc_rows = [
        {"principal": principal, "bound": enrolled.get(host, False)}
        for principal, host in _services()
    ]

    return {
        "schema_tag": "ipa-seat-v1",
        "hosts": host_rows,
        "services": svc_rows,
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
    Path("/var/lib/ipa/state/seat_pass_a.bin").write_bytes(first)
    Path("/var/lib/ipa/state/seat_pass_b.bin").write_bytes(second)


def _doc() -> dict:
    assert OUT.is_file(), "missing /output/ipa-seat.json"
    return json.loads(OUT.read_text())


def test_q3_topaz() -> None:
    """Ledger schema, schema_tag, and seat_ok."""
    doc = _doc()
    assert doc["schema_tag"] == "ipa-seat-v1"
    assert isinstance(doc["hosts"], list) and len(doc["hosts"]) == len(_hosts())
    assert isinstance(doc["services"], list) and len(doc["services"]) == len(_services())
    assert doc["seat_ok"] is True
    for h in doc["hosts"]:
        assert set(h) >= {"name", "realm", "keytab", "generation", "enrolled"}
        assert isinstance(h["generation"], int)
        assert isinstance(h["enrolled"], bool)
    for s in doc["services"]:
        assert set(s) >= {"principal", "bound"}
        assert isinstance(s["bound"], bool)


def test_n4_beryl() -> None:
    """Two seating passes leave byte-identical output."""
    a = Path("/var/lib/ipa/state/seat_pass_a.bin").read_bytes()
    b = Path("/var/lib/ipa/state/seat_pass_b.bin").read_bytes()
    assert a and b and a == b


def test_w7_quartz() -> None:
    """Frozen keytab samples under /app/data/ipa remain packaging-pinned."""
    pin = Path("/app/packaging/ipa.sha256")
    assert pin.is_file()
    proc = subprocess.run(
        ["sha256sum", "-c", "/app/packaging/ipa.sha256"],
        cwd="/app/data/ipa",
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_j2_onyx() -> None:
    """Lexical realm fold selects the site-standard realm."""
    _run_seat()
    eff = _load_kv(EFF)
    site = _load_kv(SITE)
    assert eff.get("realm") == site.get("realm")
    assert "SURFACE-DECOY" not in (eff.get("realm") or "")
    doc = _doc()
    for h in doc["hosts"]:
        assert h["realm"] == site.get("realm")


def test_v5_coral() -> None:
    """Generation vs durable floor polarity across the roster."""
    doc = _doc()
    exp = {h["name"]: h for h in _expected_doc()["hosts"]}
    for h in doc["hosts"]:
        e = exp[h["name"]]
        assert h["generation"] == e["generation"]
        floor = int((FLOOR_D / f"{h['name']}.floor").read_text().strip())
        if h["generation"] < floor:
            assert h["enrolled"] is False


def test_p9_jade() -> None:
    """Active SSSD abort blocks enrollment; expired abort does not."""
    doc = _doc()
    by_name = {h["name"]: h for h in doc["hosts"]}
    clock = int(CLOCK.read_text().strip())
    abort = _abort_until()
    assert abort["cache01"] > clock
    assert abort["mail01"] <= clock
    assert by_name["cache01"]["enrolled"] is False
    assert by_name["mail01"]["enrolled"] is True


def test_h8_amber() -> None:
    """Surface realm forensic; live SSSD realm not decoy; prefer.accept matches tip."""
    assert SURFACE.is_file()
    assert "SURFACE-DECOY" in SURFACE.read_text()
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    assert TIP_ID.is_file()
    assert kv.get("tip") == TIP_ID.read_text().strip()
    sssd = SSSD.read_text()
    assert "SURFACE-DECOY" not in sssd
    assert "LAB.EXAMPLE.ORG" in sssd
    doc = _doc()
    for h in doc["hosts"]:
        assert "SURFACE-DECOY" not in h["realm"]


def test_c1_flint() -> None:
    """prefer.accept tip id aligned; gen.live equals gen.target."""
    assert RECEIPT.is_file()
    kv = _load_kv(RECEIPT)
    sealed = _sealed()
    assert kv.get("tip") == sealed.get("tip_id")
    live = Path("/var/lib/ipa/state/gen.live").read_text().strip()
    assert live == GEN_TARGET.read_text().strip()


def test_r6_slate() -> None:
    """Every host keytab equals the durable sealed tip fingerprint."""
    doc = _doc()
    exp = {h["name"]: h for h in _expected_doc()["hosts"]}
    for h in doc["hosts"]:
        assert h["keytab"] == exp[h["name"]]["keytab"]
        assert "live" not in h["keytab"]


def test_u2_mica() -> None:
    """Service bound array matches host enrollment; seat_ok stays true."""
    doc = _doc()
    exp = _expected_doc()
    got = sorted(doc["services"], key=lambda s: s["principal"])
    want = sorted(exp["services"], key=lambda s: s["principal"])
    assert got == want
    assert doc["seat_ok"] is True


def test_m1_opal() -> None:
    """Full roster enrolled matrix against durable authority."""
    doc = _doc()
    exp = {h["name"]: h for h in _expected_doc()["hosts"]}
    assert sorted(h["name"] for h in doc["hosts"]) == sorted(exp)
    for h in doc["hosts"]:
        e = exp[h["name"]]
        assert h["enrolled"] == e["enrolled"], h["name"]
        assert h["generation"] == e["generation"]
        assert h["realm"] == e["realm"]
        assert h["keytab"] == e["keytab"]
    by_name = {h["name"]: h for h in doc["hosts"]}
    assert by_name["web01"]["enrolled"] is True
    assert by_name["db01"]["enrolled"] is False
    assert by_name["cache01"]["enrolled"] is False
    assert by_name["mail01"]["enrolled"] is True
    assert by_name["log01"]["enrolled"] is True


def test_t4_pearl() -> None:
    """Surface ipahealth may print joined; deep seating still required."""
    proc = subprocess.run(
        ["/usr/local/bin/ipahealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "joined" in proc.stdout
    doc = _doc()
    assert doc["seat_ok"] is True
    assert doc["schema_tag"] == "ipa-seat-v1"


def test_k5_garnet() -> None:
    """Novel sealed-journal tip inject shifts keytab and generation together."""
    sealed = {
        "kind": "seal",
        "gen": 8,
        "mode": "seal",
        "tip_id": "tip_g8",
        "realm": "LAB.EXAMPLE.ORG",
        "tips": {
            "web01": {"fpr": "aa11bb22cc33", "gen": 6},
            "db01": {"fpr": "dd44ee55ff66", "gen": 2},
            "cache01": {"fpr": "1122334455aa", "gen": 6},
            "mail01": {"fpr": "6677889900bb", "gen": 6},
            "log01": {"fpr": "ccddeeff0011", "gen": 6},
        },
    }
    with JOURNAL.open("a") as fh:
        fh.write(json.dumps(sealed) + "\n")
    GEN_TARGET.write_text("8\n")
    RECEIPT.write_text("tip=tip_g8\n")
    _run_seat()
    doc = _doc()
    by_name = {h["name"]: h for h in doc["hosts"]}
    assert by_name["web01"]["keytab"] == sealed["tips"]["web01"]["fpr"]
    assert by_name["web01"]["generation"] == sealed["tips"]["web01"]["gen"]
    assert by_name["web01"]["enrolled"] is True
    assert by_name["db01"]["generation"] == sealed["tips"]["db01"]["gen"]
    assert by_name["db01"]["enrolled"] is False
    assert by_name["cache01"]["enrolled"] is False
    assert Path("/var/lib/ipa/state/gen.live").read_text().strip() == str(sealed["gen"])
    assert _load_kv(RECEIPT).get("tip") == sealed["tip_id"]
