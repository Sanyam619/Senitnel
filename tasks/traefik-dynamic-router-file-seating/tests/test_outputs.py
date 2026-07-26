"""Verifier for Traefik dynamic router file seating.

Re-enters /app/ops/run_traefik_seat.sh and derives EXPECTED seating from
durable fixtures under /app/data and /var/lib/traefik — not from agent output
alone.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/traefik-seat.json")
DATA = Path("/app/data/traefik")
PIN = Path("/app/packaging/traefik.sha256")
SITE = Path("/app/config/site_standard.yml")
ETC = Path("/etc/traefik")
VAR = Path("/var/lib/traefik")
ROSTER = ETC / "roster.list"
MW_LIST = ETC / "mw.list"


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


def _mw_names() -> list[str]:
    return [ln.strip() for ln in MW_LIST.read_text().splitlines() if ln.strip()]


def _retired() -> set[str]:
    out: set[str] = set()
    for line in (VAR / "ops" / "retired_tips.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        out.add(json.loads(line)["tip"])
    return out


def _journal_tips() -> dict[str, dict]:
    retired = _retired()
    target = (VAR / "ops" / "state" / "gen.target").read_text().strip()
    tips: dict[str, dict] = {}
    tip_id = None
    seal_ok = False
    for line in (VAR / "ops" / "journal.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "seal" and str(row.get("gen")) == target:
            seal_ok = True
        if row.get("tag") != "tip":
            continue
        if row.get("kind") != "durable":
            continue
        if row.get("tip") in retired:
            continue
        tip_id = row.get("tip")
        tips[str(row["name"])] = {
            "rule": row["rule"],
            "service": row["service"],
            "generation": int(row["generation"]),
            "tip": tip_id,
        }
    assert seal_ok, "missing sealed journal row"
    assert tip_id, "no durable tip"
    return tips


def _floors() -> dict[str, int]:
    out: dict[str, int] = {}
    for name in _roster():
        out[name] = int((VAR / "ops" / "floors" / f"{name}.floor").read_text().strip())
    return out


def _mw_prefer() -> list[dict]:
    kv = _parse_kv((VAR / "ops" / "mw_prefer.toml").read_text())
    rows = []
    for name in _mw_names():
        rows.append(
            {
                "name": name,
                "type": kv.get(f"type.{name}", name),
                "attached": kv.get(f"attach.{name}", "false") == "true",
            }
        )
    return rows


def _expected_routers() -> list[dict]:
    tips = _journal_tips()
    floors = _floors()
    rows = []
    for name in _roster():
        tip = tips[name]
        gen = tip["generation"]
        rows.append(
            {
                "name": name,
                "rule": tip["rule"],
                "service": tip["service"],
                "generation": gen,
                "active": gen >= floors[name],
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
        ["/bin/bash", "/app/ops/run_traefik_seat.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/traefik-seat.json"
    return json.loads(REPORT.read_text())


def test_q3_topaz():
    """Ledger schema, schema_tag, and seat_ok after seating."""
    doc = _reseat()
    assert doc["schema_tag"] == "traefik-seat-v1"
    assert isinstance(doc["routers"], list)
    assert isinstance(doc["middlewares"], list)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"]
    needed_r = {"name", "rule", "service", "generation", "active"}
    needed_m = {"name", "type", "attached"}
    for row in doc["routers"]:
        assert needed_r <= set(row)
        assert isinstance(row["generation"], int)
        assert isinstance(row["active"], bool)
    for row in doc["middlewares"]:
        assert needed_m <= set(row)
        assert isinstance(row["attached"], bool)


def test_n4_beryl():
    """Two seating runs leave byte-identical ledger bytes."""
    _reseat()
    first = REPORT.read_bytes()
    _reseat()
    second = REPORT.read_bytes()
    assert first == second
    assert first.endswith(b"\n")


def test_w7_quartz():
    """Frozen traefik fixtures stay integrity-pinned."""
    assert PIN.is_file()
    expected = {}
    for line in PIN.read_text().splitlines():
        if not line.strip():
            continue
        digest, path = line.split(None, 1)
        expected[Path(path).name] = digest
    assert expected, "empty packaging pin"
    for name, digest in expected.items():
        got = _file_sha256(DATA / name)
        assert got == digest, f"fixture drift on {name}"


def test_j2_onyx():
    """Router rule/service match durable journal tip, not live decoy."""
    doc = _reseat()
    tips = _journal_tips()
    by_name = {r["name"]: r for r in doc["routers"]}
    for name, tip in tips.items():
        assert by_name[name]["rule"] == tip["rule"]
        assert by_name[name]["service"] == tip["service"]
        assert "live" not in by_name[name]["rule"]
        assert by_name[name]["service"] != "svc-live"


def test_v5_coral():
    """Generation equals journal tip; floor polarity drives active."""
    doc = _reseat()
    tips = _journal_tips()
    floors = _floors()
    by_name = {r["name"]: r for r in doc["routers"]}
    for name, tip in tips.items():
        assert by_name[name]["generation"] == tip["generation"]
        want_active = tip["generation"] >= floors[name]
        assert by_name[name]["active"] is want_active
    assert by_name["beta"]["generation"] < floors["beta"]
    assert by_name["beta"]["active"] is False
    assert by_name["alpha"]["generation"] >= floors["alpha"]
    assert by_name["alpha"]["active"] is True
    assert by_name["epsilon"]["active"] is False
    assert by_name["delta"]["active"] is True
    assert doc["seat_ok"]
    assert (VAR / "ops" / "state" / "gen.live").read_text().strip() == (
        VAR / "ops" / "state" / "gen.target"
    ).read_text().strip()


def test_p9_jade():
    """Middleware attached flags follow durable prefer sheet."""
    doc = _reseat()
    expected = {r["name"]: r for r in _mw_prefer()}
    by_name = {r["name"]: r for r in doc["middlewares"]}
    assert set(by_name) == set(expected)
    for name, exp in expected.items():
        assert by_name[name]["type"] == exp["type"]
        assert by_name[name]["attached"] is exp["attached"]
    assert by_name["ratelimit"]["attached"] is False
    assert by_name["compress"]["attached"] is True
    assert by_name["headers"]["attached"] is True


def test_h8_amber():
    """Abort package stays forensic; live drop-in is site-standard."""
    _reseat()
    abort_kv = _parse_kv((VAR / "ops" / "abort.d" / "90-abort.yml").read_text())
    live_kv = _parse_kv((ETC / "dynamic" / "90-local.yml").read_text())
    site = _parse_kv(SITE.read_text())
    assert abort_kv.get("tip_policy") == "prefer_abort"
    assert abort_kv.get("abort_token") == "revoke_all"
    assert live_kv.get("tip_policy") == site.get("tip_policy")
    assert live_kv.get("abort_token") == site.get("abort_token")
    assert abort_kv.get("tip_policy") != live_kv.get("tip_policy")


def test_c1_flint():
    """Matching cutover.ok receipt; live 90-local remains present."""
    _reseat()
    receipt = VAR / "ops" / "state" / "cutover.ok"
    assert receipt.is_file()
    rkv = _parse_kv(receipt.read_text())
    target = (VAR / "ops" / "state" / "gen.target").read_text().strip()
    assert rkv.get("gen") == target
    assert rkv.get("mode") == "seal"
    live = ETC / "dynamic" / "90-local.yml"
    assert live.is_file()
    assert live.stat().st_size > 0
    assert "revoke.alpha=true" not in live.read_text()


def test_r6_slate():
    """Abort fragment does not revoke correctly seated routers."""
    doc = _reseat()
    by_name = {r["name"]: r for r in doc["routers"]}
    # alpha/gamma/delta meet floor — must stay active despite abort residue package
    assert by_name["alpha"]["active"] is True
    assert by_name["gamma"]["active"] is True
    assert by_name["delta"]["active"] is True
    # forensic abort still contains revoke synonyms
    abort = (VAR / "ops" / "abort.d" / "90-abort.yml").read_text()
    assert "revoke.alpha=true" in abort
    assert doc["seat_ok"]


def test_u2_mica():
    """Routers and middlewares match durable EXPECTED and couple to seat_ok."""
    doc = _reseat()
    assert doc["seat_ok"]
    assert doc["routers"] == _expected_routers()
    assert doc["middlewares"] == _mw_prefer()


def test_m1_opal():
    """Full roster active/inactive matrix."""
    doc = _reseat()
    expected = _expected_routers()
    assert [r["name"] for r in doc["routers"]] == [r["name"] for r in expected]
    for got, exp in zip(doc["routers"], expected, strict=True):
        assert got == exp
    by_name = {r["name"]: r for r in doc["routers"]}
    assert by_name["beta"]["active"] is False
    assert by_name["epsilon"]["active"] is False
    assert by_name["alpha"]["active"] is True


def test_t4_pearl():
    """Surface traefikhealth may look fine while deep seating is graded."""
    doc = _reseat()
    assert doc["seat_ok"]
    proc = subprocess.run(
        ["/usr/local/bin/traefikhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "routed"


def test_s8_garnet():
    """Flipping prefer back to live rematerializes decoy routers on re-seat."""
    _reseat()
    prefer = VAR / "ops" / "prefer.toml"
    original = prefer.read_text()
    try:
        prefer.write_text('[selection]\nsource = "live"\nmode = "surface"\n')
        doc = _reseat()
        by_name = {r["name"]: r for r in doc["routers"]}
        assert "live" in by_name["alpha"]["rule"] or by_name["alpha"]["service"] == "svc-live"
        assert doc["seat_ok"] is False
    finally:
        prefer.write_text(original)
        _reseat()


def test_d6_obsidian():
    """Novel durable tip inject moves rule and generation on re-seat."""
    _reseat()
    journal = VAR / "ops" / "journal.jsonl"
    original = journal.read_text()
    try:
        # Append a newer durable tip row for alpha and bump seal/target.
        (VAR / "ops" / "state" / "gen.target").write_text("8\n")
        extra = (
            '{"tag":"tip","tip":"tip_g8","name":"alpha",'
            '"rule":"Host(`alpha.lab8`)","service":"svc-alpha8",'
            '"generation":8,"kind":"durable"}\n'
            '{"tag":"tip","tip":"tip_g8","name":"beta",'
            '"rule":"Host(`beta.lab`)","service":"svc-beta",'
            '"generation":8,"kind":"durable"}\n'
            '{"tag":"tip","tip":"tip_g8","name":"gamma",'
            '"rule":"Host(`gamma.lab`)","service":"svc-gamma",'
            '"generation":8,"kind":"durable"}\n'
            '{"tag":"tip","tip":"tip_g8","name":"delta",'
            '"rule":"Host(`delta.lab`)","service":"svc-delta",'
            '"generation":8,"kind":"durable"}\n'
            '{"tag":"tip","tip":"tip_g8","name":"epsilon",'
            '"rule":"Host(`epsilon.lab`)","service":"svc-epsilon",'
            '"generation":8,"kind":"durable"}\n'
            '{"tag":"seal","gen":"8"}\n'
        )
        journal.write_text(original + extra)
        # Binding must track the new serving tip for knit gate.
        (VAR / "ops" / "tip_bind.accept").write_text("tip_g8\n")
        doc = _reseat()
        by_name = {r["name"]: r for r in doc["routers"]}
        assert by_name["alpha"]["rule"] == "Host(`alpha.lab8`)"
        assert by_name["alpha"]["service"] == "svc-alpha8"
        assert by_name["alpha"]["generation"] == 8
        assert by_name["alpha"]["active"] is True
        assert doc["seat_ok"]
    finally:
        journal.write_text(original)
        (VAR / "ops" / "state" / "gen.target").write_text("7\n")
        (VAR / "ops" / "tip_bind.accept").write_text("tip_g7\n")
        _reseat()
