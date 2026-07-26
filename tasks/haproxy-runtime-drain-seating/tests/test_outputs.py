"""Verifier for HAProxy runtime-drain backend seating.

Re-enters /app/ops/run_proxy_seat.sh and derives EXPECTED seating from
durable fixtures under /app/data and /var/lib/haproxy — not from agent output
alone.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/proxy-seat.json")
DATA_BACKENDS = Path("/app/data/backends")
PIN = Path("/app/packaging/backends.sha256")
SITE = Path("/app/config/site_standard.conf")
ETC = Path("/etc/haproxy")
VAR = Path("/var/lib/haproxy")
RUN = Path("/var/run/haproxy")
ROSTER = ETC / "roster.list"


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


def _site_weights() -> dict[str, int]:
    kv = _parse_kv(SITE.read_text())
    return {
        name: int(kv[f"weight.{name}"])
        for name in _roster()
        if f"weight.{name}" in kv
    }


def _journal_tips() -> dict[str, int]:
    tips: dict[str, int] = {}
    target = (VAR / "state" / "gen.target").read_text().strip()
    seal_ok = False
    for line in (VAR / "ops" / "journal.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "seal" and str(row.get("gen")) == target:
            seal_ok = True
        if row.get("tag") == "tip":
            tips[str(row["name"])] = int(row["generation"])
    assert seal_ok
    return tips


def _expect_drained(name: str) -> bool:
    clock = int((VAR / "state" / "clock.epoch").read_text().strip())
    lease = VAR / "leases" / f"{name}.lease"
    if not lease.exists():
        return False
    until_epoch = int(_parse_kv(lease.read_text()).get("until_epoch", "0"))
    return until_epoch > clock


def _durable_server(name: str) -> str:
    fixture = DATA_BACKENDS / f"{name}.toml"
    for line in fixture.read_text().splitlines():
        if line.strip().startswith("server"):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError(f"missing server in {fixture}")


def _expected_backends() -> list[dict]:
    tips = _journal_tips()
    weights = _site_weights()
    rows = []
    for name in _roster():
        rows.append(
            {
                "name": name,
                "server": _durable_server(name),
                "weight": weights[name],
                "drained": _expect_drained(name),
                "generation": tips[name],
            }
        )
    return rows


def _file_sha256(path: Path) -> str:
    proc = subprocess.run(
        ["sha256sum", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.split()[0]


def _reseat() -> dict:
    REPORT.unlink(missing_ok=True)
    proc = subprocess.run(
        ["/bin/bash", "/app/ops/run_proxy_seat.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/proxy-seat.json"
    return json.loads(REPORT.read_text())


def test_q3_topaz():
    """Ledger schema, schema_tag, and seat_ok after seating."""
    doc = _reseat()
    assert doc["schema_tag"] == "proxy-seat-v1"
    assert isinstance(doc["backends"], list)
    assert isinstance(doc["socket_applied"], bool)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"]
    assert doc["socket_applied"]
    needed = {"name", "server", "weight", "drained", "generation"}
    for row in doc["backends"]:
        assert needed <= set(row)
        assert isinstance(row["weight"], int)
        assert isinstance(row["drained"], bool)
        assert isinstance(row["generation"], int)


def test_n4_beryl():
    """Two seating runs leave byte-identical ledger bytes."""
    _reseat()
    first = REPORT.read_bytes()
    _reseat()
    second = REPORT.read_bytes()
    assert first == second
    assert first.endswith(b"\n")


def test_w7_quartz():
    """Frozen backend fixtures stay integrity-pinned."""
    assert PIN.is_file()
    expected = {}
    for line in PIN.read_text().splitlines():
        if not line.strip():
            continue
        digest, path = line.split(None, 1)
        expected[Path(path).name] = digest
    assert expected, "empty packaging pin"
    for name, digest in expected.items():
        got = _file_sha256(DATA_BACKENDS / name)
        assert got == digest, f"fixture drift on {name}"


def test_j2_onyx():
    """Folded effective weights match site-standard tokens."""
    doc = _reseat()
    weights = _site_weights()
    by_name = {r["name"]: r for r in doc["backends"]}
    for name, w in weights.items():
        assert by_name[name]["weight"] == w
    eff = _parse_kv((VAR / "state" / "effective.conf").read_text())
    site = _parse_kv(SITE.read_text())
    assert eff.get("tip_policy") == site.get("tip_policy")
    assert eff.get("bind_order") == site.get("bind_order")
    for name in _roster():
        assert eff.get(f"weight.{name}") == site.get(f"weight.{name}")


def test_v5_coral():
    """Generation equals raw journal tip; floor polarity is reported only."""
    doc = _reseat()
    tips = _journal_tips()
    by_name = {r["name"]: r for r in doc["backends"]}
    for name, gen in tips.items():
        assert by_name[name]["generation"] == gen
    beta_floor = int((VAR / "floors" / "beta.floor").read_text().strip())
    alpha_floor = int((VAR / "floors" / "alpha.floor").read_text().strip())
    # Below-floor tip is still reported; seat_ok remains true when otherwise agreed.
    assert by_name["beta"]["generation"] < beta_floor
    assert by_name["alpha"]["generation"] >= alpha_floor
    assert doc["seat_ok"]
    assert (VAR / "state" / "gen.live").read_text().strip() == (
        VAR / "state" / "gen.target"
    ).read_text().strip()


def test_p9_jade():
    """Active drain lease marks drained without zeroing weight."""
    doc = _reseat()
    by_name = {r["name"]: r for r in doc["backends"]}
    assert by_name["gamma"]["drained"]
    assert by_name["gamma"]["weight"] == _site_weights()["gamma"]
    assert by_name["gamma"]["weight"] != 0
    assert not by_name["alpha"]["drained"]


def test_h8_amber():
    """Abort package stays forensic; live drop-in is site-standard."""
    _reseat()
    abort_kv = _parse_kv((VAR / "ops" / "abort.d" / "90-local.cfg").read_text())
    live_kv = _parse_kv((ETC / "conf.d" / "90-local.cfg").read_text())
    site = _parse_kv(SITE.read_text())
    # Forensic abort synonyms must differ from live site-standard weights.
    assert abort_kv.get("weight.delta") != live_kv.get("weight.delta")
    assert live_kv.get("tip_policy") == site.get("tip_policy")
    assert live_kv.get("weight.delta") == site.get("weight.delta")
    assert abort_kv.get("tip_policy") == "prefer_abort"
    assert abort_kv.get("weight.delta") == "999"


def test_c1_flint():
    """Matching cutover.ok receipt; live 90-local remains present."""
    _reseat()
    receipt = VAR / "state" / "cutover.ok"
    assert receipt.is_file()
    rkv = _parse_kv(receipt.read_text())
    target = (VAR / "state" / "gen.target").read_text().strip()
    assert rkv.get("gen") == target
    assert rkv.get("mode") == "seal"
    live = ETC / "conf.d" / "90-local.cfg"
    assert live.is_file()
    assert live.stat().st_size > 0


def test_r6_slate():
    """Runtime socket apply matches folded weights and drain flags."""
    doc = _reseat()
    assert doc["socket_applied"]
    expected = {r["name"]: r for r in _expected_backends()}
    lines = {}
    for line in (RUN / "runtime.map").read_text().splitlines():
        parts = line.split()
        assert len(parts) >= 3
        lines[parts[0]] = (int(parts[1]), int(parts[2]))
    for name, row in expected.items():
        want = (row["weight"], 1 if row["drained"] else 0)
        assert lines[name] == want


def test_u2_mica():
    """Backends array matches durable EXPECTED and couples to seat_ok."""
    doc = _reseat()
    assert doc["seat_ok"]
    assert doc["backends"] == _expected_backends()


def test_m1_opal():
    """Full roster weight/drain/generation matrix."""
    doc = _reseat()
    expected = _expected_backends()
    assert [r["name"] for r in doc["backends"]] == [r["name"] for r in expected]
    for got, exp in zip(doc["backends"], expected, strict=True):
        assert got == exp
    by_name = {r["name"]: r for r in doc["backends"]}
    exp = {r["name"]: r for r in expected}
    assert by_name["beta"]["generation"] == exp["beta"]["generation"]
    assert by_name["gamma"]["drained"]
    assert by_name["delta"]["weight"] == exp["delta"]["weight"]


def test_t4_pearl():
    """Surface proxyhealth may look fine while deep seating is graded."""
    doc = _reseat()
    assert doc["seat_ok"]
    proc = subprocess.run(
        ["/usr/local/bin/proxyhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "UP"


def test_s8_garnet():
    """socket_applied and seat_ok go false when runtime apply is stripped."""
    _reseat()
    (RUN / "runtime.map").unlink(missing_ok=True)
    (RUN / "socket.applied").unlink(missing_ok=True)
    proc = subprocess.run(
        ["/bin/bash", "/app/deck/emit_m.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    doc = json.loads(REPORT.read_text())
    assert doc["socket_applied"] is False
    assert doc["seat_ok"] is False


def test_d6_obsidian():
    """Ledger follows a durable site-standard weight change on re-seat."""
    _reseat()
    original = SITE.read_text()
    try:
        assert "weight.alpha=100" in original
        SITE.write_text(original.replace("weight.alpha=100", "weight.alpha=77"))
        doc = _reseat()
        by_name = {r["name"]: r for r in doc["backends"]}
        assert by_name["alpha"]["weight"] == 77
        assert doc["seat_ok"]
    finally:
        SITE.write_text(original)
