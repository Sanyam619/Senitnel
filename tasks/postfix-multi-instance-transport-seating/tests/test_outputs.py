"""Verifier for Postfix multi-instance transport seating.

Re-enters /app/ops/run_postfix_seat.sh and derives EXPECTED seating from
durable fixtures under /app/data and /var/lib/postfix — not from agent
output alone.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/postfix-seat.json")
DATA_INST = Path("/app/data/postfix")
SITE = Path("/app/config/site_standard.conf")
ETC = Path("/etc/postfix")
VAR = Path("/var/lib/postfix")
OPS = VAR / "ops"
ROSTER = ETC / "roster.list"
ALLOWED_PREF = {"durable", "authority"}
PREFER_MAP = "hash:/var/lib/postfix/ops/maps/nexthop.prefer"
PACKAGING = Path("/app") / "packaging" / "instances.sha256"


def _parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _parse_main(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _roster() -> list[str]:
    return [ln.strip() for ln in ROSTER.read_text().splitlines() if ln.strip()]


def _prefer_tip() -> dict[str, dict]:
    target = (VAR / "state" / "gen.target").read_text().strip()
    batches: list[dict] = []
    seal_ok = False
    for line in (VAR / "ops" / "prefer.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "seal" and str(row.get("gen")) == target:
            seal_ok = True
        if row.get("tag") == "batch":
            batches.append(row)
    assert seal_ok, "prefer journal missing seal for gen.target"
    chosen = None
    for batch in batches:
        if str(batch.get("gen")) != target:
            continue
        if batch.get("sealed") is True and batch.get("complete") is True:
            chosen = batch
    assert chosen is not None, "no sealed complete prefer batch"
    return {
        row["name"]: {
            "queue_dir": row["queue_dir"],
            "generation": int(target),
        }
        for row in chosen["rows"]
    }


def _journal_eligible() -> set[str]:
    target = (VAR / "state" / "gen.target").read_text().strip()
    admitted: set[str] = set()
    revoked: set[str] = set()
    seal_ok = False
    for line in (VAR / "ops" / "instances.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "seal" and str(row.get("gen")) == target:
            seal_ok = True
        if str(row.get("gen")) != target:
            continue
        name = row.get("name")
        if not name:
            continue
        if row.get("tag") == "admit":
            admitted.add(str(name))
        elif row.get("tag") == "revoke":
            revoked.add(str(name))
    assert seal_ok
    return admitted - revoked


def _abort_patterns() -> set[str]:
    found: set[str] = set()
    path = OPS / "abort.d" / "90-local.cf"
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" in line and line.split("=", 1)[0] in {
            "mail_policy",
            "bind_order",
            "transport_maps",
        }:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2 and ("." in parts[0] or parts[0].startswith(".")):
            found.add(parts[0])
    return found


def _prefer_map_rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    path = OPS / "maps" / "nexthop.prefer"
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            rows.append((parts[0], parts[1]))
    return rows


def _floor(name: str) -> int:
    return int((VAR / "floors" / f"{name}.floor").read_text().strip())


def _durable_queue(name: str) -> str:
    tip = _prefer_tip()
    return tip[name]["queue_dir"]


def _expected_instances() -> list[dict]:
    tip = _prefer_tip()
    eligible = _journal_eligible()
    rows = []
    for name in _roster():
        t = tip[name]
        active = name in eligible and t["generation"] >= _floor(name)
        rows.append(
            {
                "name": name,
                "queue_dir": t["queue_dir"],
                "generation": t["generation"],
                "active": active,
            }
        )
    return rows


def _expected_transports() -> list[dict]:
    aborts = _abort_patterns()
    return [
        {
            "pattern": pattern,
            "nexthop": nexthop,
            "honored": pattern not in aborts,
        }
        for pattern, nexthop in _prefer_map_rows()
    ]


def _prefer_mode() -> str:
    text = (OPS / "prefer.toml").read_text()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("mode"):
            return line.split("=", 1)[1].strip().strip('"')
    return "live"


def _fixture_digests() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in PACKAGING.read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        out[name.strip().lstrip("./")] = digest
    return out


def _reseat() -> dict:
    REPORT.unlink(missing_ok=True)
    proc = subprocess.run(
        ["/bin/bash", "/app/ops/run_postfix_seat.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/postfix-seat.json"
    return json.loads(REPORT.read_text())


def test_q3_topaz():
    """Ledger schema, schema_tag, seat_ok, and active polarity after seating."""
    doc = _reseat()
    assert doc["schema_tag"] == "postfix-seat-v1"
    assert isinstance(doc["instances"], list)
    assert isinstance(doc["transports"], list)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"] is True
    needed = {"name", "queue_dir", "generation", "active"}
    for row in doc["instances"]:
        assert needed <= set(row)
        assert isinstance(row["generation"], int)
        assert isinstance(row["active"], bool)
        assert row["queue_dir"].startswith("/var/spool/postfix-")
        assert not row["queue_dir"].endswith("-decoy")
        assert not row["queue_dir"].endswith("-surface")
    for row in doc["transports"]:
        assert {"pattern", "nexthop", "honored"} <= set(row)
        assert isinstance(row["honored"], bool)
        assert "decoy" not in row["nexthop"]
        assert "surface" not in row["nexthop"]
    by_name = {p["name"]: p for p in doc["instances"]}
    assert by_name["mesa"]["active"] is True
    assert by_name["ridge"]["active"] is True
    assert by_name["beacon"]["active"] is False
    assert by_name["cinder"]["active"] is False
    assert by_name["quay"]["active"] is True
    assert _prefer_mode() in ALLOWED_PREF
    bind = _parse_kv((OPS / "tip_bind.accept").read_text())
    assert bind.get("gen") == (VAR / "state" / "gen.target").read_text().strip()


def test_n4_beryl():
    """Two seating runs leave byte-identical ledger bytes."""
    _reseat()
    first = REPORT.read_bytes()
    _reseat()
    second = REPORT.read_bytes()
    assert first == second
    assert first.endswith(b"\n")
    assert (VAR / "state" / "gen.live").read_text().strip() == (
        VAR / "state" / "gen.target"
    ).read_text().strip()


def test_w7_quartz():
    """Frozen instance fixtures stay pinned and tip queues match durable batch."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    by_name = {p["name"]: p for p in doc["instances"]}
    tip = _prefer_tip()
    digests = _fixture_digests()
    for name in _roster():
        fixture = DATA_INST / f"{name}.toml"
        assert fixture.is_file(), name
        text = fixture.read_text()
        assert f'name = "{name}"' in text
        assert f'queue_dir = "{tip[name]["queue_dir"]}"' in text
        assert digests[f"{name}.toml"]
        tip_queue = (VAR / "state" / f"tip_{name}.queue").read_text().strip()
        tip_gen = int((VAR / "state" / f"tip_{name}.gen").read_text().strip())
        assert tip_queue == tip[name]["queue_dir"]
        assert tip_gen == tip[name]["generation"]
        assert by_name[name]["queue_dir"] == tip_queue
        assert by_name[name]["generation"] == tip_gen


def test_v5_coral():
    """Sealed complete prefer tip beats incomplete later decoy queue paths."""
    doc = _reseat()
    by_name = {p["name"]: p for p in doc["instances"]}
    tip = _prefer_tip()
    assert by_name["mesa"]["queue_dir"] == tip["mesa"]["queue_dir"]
    assert by_name["mesa"]["queue_dir"].endswith("/postfix-mesa")
    assert not by_name["mesa"]["queue_dir"].endswith("-decoy")
    assert not by_name["mesa"]["queue_dir"].endswith("-wrong")
    assert by_name["beacon"]["queue_dir"] == tip["beacon"]["queue_dir"]
    assert not by_name["beacon"]["queue_dir"].endswith("-decoy")


def test_p9_jade():
    """Revoked journal instance is never active."""
    doc = _reseat()
    by_name = {p["name"]: p for p in doc["instances"]}
    assert by_name["cinder"]["active"] is False
    assert "cinder" not in _journal_eligible()


def test_h8_amber():
    """Abort package stays forensic while live master.d is site-standard."""
    _reseat()
    abort_kv = _parse_kv((VAR / "ops" / "abort.d" / "90-local.cf").read_text())
    live_kv = _parse_kv((ETC / "master.d" / "90-local.cf").read_text())
    site_kv = _parse_kv(SITE.read_text())
    assert abort_kv.get("mail_policy") == "prefer_abort"
    assert "collide.lab" in (VAR / "ops" / "abort.d" / "90-local.cf").read_text()
    assert live_kv.get("mail_policy") == "prefer_relay"
    assert live_kv.get("mail_policy") == site_kv["mail_policy"]
    assert live_kv.get("bind_order") == site_kv["bind_order"]
    assert live_kv.get("transport_maps") == site_kv["transport_maps"]
    assert live_kv != abort_kv


def test_c1_flint():
    """Matching cutover receipt skips rematerialize; live drop-in remains."""
    _reseat()
    receipt = VAR / "state" / "cutover.ok"
    assert receipt.is_file()
    rkv = _parse_kv(receipt.read_text())
    target = (VAR / "state" / "gen.target").read_text().strip()
    assert rkv.get("gen") == target
    assert rkv.get("mode") == "seal"
    live = ETC / "master.d" / "90-local.cf"
    assert live.is_file()
    assert live.read_text().strip()
    receipt.write_text("gen=3\nmode=live\n")
    _reseat()
    live_after = _parse_kv(live.read_text())
    assert (VAR / "ops" / "abort.d" / "90-local.cf").is_file()
    assert live_after.get("mail_policy") == "prefer_relay"


def test_r6_slate():
    """Transport collide.lab is folded but honored=false from abort fragment."""
    doc = _reseat()
    by_pat = {t["pattern"]: t for t in doc["transports"]}
    assert "collide.lab" in by_pat
    assert by_pat["collide.lab"]["honored"] is False
    assert by_pat["collide.lab"]["nexthop"] == "smtp:[smtp.prefer.internal]"
    assert by_pat[".example.com"]["honored"] is True
    assert by_pat["lab.corp"]["honored"] is True
    assert by_pat["orphan.lab"]["honored"] is True
    assert "collide.lab" in _abort_patterns()


def test_j2_onyx():
    """Folded transports match prefer nexthop map × abort honor polarity."""
    doc = _reseat()
    assert doc["transports"] == _expected_transports()
    for row in doc["transports"]:
        assert "live.decoy" not in row["nexthop"]
        assert "bait" not in row["nexthop"]
        assert "surface.decoy" not in row["nexthop"]
    working = (OPS / "maps" / "nexthop.prefer").read_text()
    durable = (OPS / "maps" / "nexthop.durable").read_text()
    assert "mx.prefer.internal" in working
    assert "mx.prefer.internal" in durable
    assert working == durable


def test_m1_opal():
    """Full roster matrix matches durable tip × journal × floor."""
    doc = _reseat()
    assert doc["instances"] == _expected_instances()
    assert doc["seat_ok"] is True


def test_u2_mica():
    """Beacon sits below durable floor; tip must not activate it."""
    doc = _reseat()
    by_name = {p["name"]: p for p in doc["instances"]}
    assert by_name["beacon"]["generation"] == 7
    assert _floor("beacon") == 8
    assert by_name["beacon"]["active"] is False
    assert by_name["beacon"]["queue_dir"] == _durable_queue("beacon")


def test_k5_garnet():
    """Live instance main.cf carries tip queue_dir and prefer transport_maps."""
    doc = _reseat()
    for row in doc["instances"]:
        main = _parse_main(Path(f"/etc/postfix-{row['name']}/main.cf"))
        assert main["queue_directory"] == row["queue_dir"]
        assert main["transport_maps"] == PREFER_MAP
        assert not main["queue_directory"].endswith("-decoy")
        assert "nexthop.live" not in main["transport_maps"]
        if row["name"] == "mesa":
            assert main["queue_directory"] == _durable_queue("mesa")
        if row["name"] == "cinder":
            assert row["active"] is False


def test_t4_pearl():
    """Surface postfixhealth mail-ready is not sufficient without durable seat."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    assert doc["instances"] == _expected_instances()
    proc = subprocess.run(
        ["/usr/local/bin/postfixhealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "mail-ready" in proc.stdout.lower()


def test_s8_zircon():
    """Clearing seating state and reseating reconstitutes the full matrix."""
    _reseat()
    REPORT.unlink(missing_ok=True)
    (VAR / "state" / "active.set").write_text("")
    (VAR / "state" / "transport.fold").unlink(missing_ok=True)
    (VAR / "state" / "honor.set").unlink(missing_ok=True)
    for name in _roster():
        (VAR / "state" / f"tip_{name}.queue").unlink(missing_ok=True)
        (VAR / "state" / f"tip_{name}.gen").unlink(missing_ok=True)
    doc = _reseat()
    assert doc["instances"] == _expected_instances()
    assert doc["transports"] == _expected_transports()
    assert doc["seat_ok"] is True
    durable = (OPS / "maps" / "nexthop.durable").read_text()
    assert "mx.prefer.internal" in durable
    assert "surface.decoy" not in durable


def test_y3_jasper():
    """Honor prefer.toml across live poison then durable recover."""
    doc = _reseat()
    assert doc["seat_ok"] is True
    assert _prefer_mode() in ALLOWED_PREF
    tip = _prefer_tip()
    for name in _roster():
        assert (VAR / "state" / f"tip_{name}.queue").read_text().strip() == tip[name][
            "queue_dir"
        ]
        main = _parse_main(Path(f"/etc/postfix-{name}/main.cf"))
        assert main["queue_directory"] == tip[name]["queue_dir"]
        assert main["transport_maps"] == PREFER_MAP
    # Flip preference to live and reseat — must honor live (not force durable).
    (OPS / "prefer.toml").write_text('mode = "live"\ntag_path = "surface"\n')
    broken = _reseat()
    assert _prefer_mode() == "live"
    assert broken["seat_ok"] is False
    mesa = _parse_main(Path("/etc/postfix-" + "mesa" + "/main.cf"))
    poisoned = (
        mesa.get("queue_directory", "").endswith("-surface")
        or mesa.get("queue_directory", "").endswith("-decoy")
        or "nexthop.live" in mesa.get("transport_maps", "")
        or "surface" in mesa.get("transport_maps", "")
        or "surface.decoy" in (VAR / "ops" / "maps" / "nexthop.prefer").read_text()
    )
    assert poisoned
    # Durable authority copy must survive surface rematerialize.
    durable = (OPS / "maps" / "nexthop.durable").read_text()
    assert "mx.prefer.internal" in durable
    assert "surface.decoy" not in durable
    # Live fold must not keep durable prefer nexthops after rematerialize.
    by_pat = {t["pattern"]: t for t in broken["transports"]}
    if ".example.com" in by_pat:
        assert "prefer" not in by_pat[".example.com"]["nexthop"]
    # Restore durable preference and reseat — recover without hand-editing ledger.
    (OPS / "prefer.toml").write_text('mode = "durable"\ntag_path = "authority"\n')
    recovered = _reseat()
    assert _prefer_mode() == "durable"
    assert recovered["seat_ok"] is True
    assert recovered["instances"] == _expected_instances()
    assert recovered["transports"] == _expected_transports()
    assert "mx.prefer.internal" in (OPS / "maps" / "nexthop.prefer").read_text()
