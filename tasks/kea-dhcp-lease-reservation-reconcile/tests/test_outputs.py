"""Verifier for Kea DHCP lease-reservation seating.

Re-enters /app/ops/run_dhcp_seat.sh. Uses a sealed ledger under /tests/ledgers
and independent invariants. Fixture digests live under /tests/ledgers so
rewriting /app/packaging/kea.sha256 cannot green integrity.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/dhcp-seat.json")
DATA_KEA = Path("/app/data/kea")
SEED_D = Path("/app/data/seed/kea-dhcp4.d")
SITE = Path("/app/config/site_standard.conf")
ETC = Path("/etc/kea")
VAR = Path("/var/lib/kea")
ROSTER = ETC / "roster.list"
AXLE = Path("/app/ops/axle_n.sh")

VERIFIER_PIN = Path("/tests/ledgers/kea.sha256")
SEALED_LEDGER = Path("/tests/ledgers/seat_v1.json")


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
        if row.get("tag") == "tip" and "id" in row:
            tips[str(row["id"])] = int(row["generation"])
    assert seal_ok
    return tips


def _durable_pools() -> dict[str, str]:
    return {
        sid: (VAR / "pools" / f"{sid}.pool").read_text().strip() for sid in _roster()
    }


def _floors() -> dict[str, int]:
    return {
        sid: int((VAR / "floors" / f"{sid}.floor").read_text().strip())
        for sid in _roster()
    }


def _active_leases() -> dict[str, str]:
    leases: dict[str, str] = {}
    mem = VAR / "ops" / "memfile.csv"
    for i, line in enumerate(mem.read_text().splitlines()):
        if i == 0 and line.lower().startswith("ip,"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        ip, hw, state = parts[0], parts[1].lower(), parts[2].lower()
        if state == "active":
            leases[ip] = hw
    return leases


def _fold_live_shadows() -> set[str]:
    """Shadowed prior IPs from live /etc/kea/kea-dhcp4.d (contract fold input)."""
    seen_hw: dict[str, str] = {}
    shadowed: set[str] = set()
    for f in sorted((ETC / "kea-dhcp4.d").glob("*.conf")):
        for raw in f.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if not k.startswith("reserve."):
                continue
            hw = k[len("reserve.") :]
            ip = v.split(":", 1)[0]
            if hw in seen_hw and seen_hw[hw] != ip:
                shadowed.add(seen_hw[hw])
            seen_hw[hw] = ip
    return shadowed


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
        ["/bin/bash", "/app/ops/run_dhcp_seat.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"
    assert REPORT.is_file(), "missing /output/dhcp-seat.json"
    return json.loads(REPORT.read_text())


def _sealed() -> dict:
    return json.loads(SEALED_LEDGER.read_text())


def _subnet_rows(doc: dict) -> set[tuple]:
    return {
        (int(r["id"]), str(r["pool"]), int(r["generation"])) for r in doc["subnets"]
    }


def _reservation_rows(doc: dict) -> set[tuple]:
    return {
        (str(r["hw"]), str(r["ip"]), int(r["subnet"]), bool(r["honored"]))
        for r in doc["reservations"]
    }


def _conflict_rows(doc: dict) -> set[tuple]:
    return {(str(c["ip"]), str(c["reason"])) for c in doc["conflicts"]}


def _write_receipt(gen: str, mode: str) -> None:
    (VAR / "state" / "cutover.ok").write_text(f"gen={gen}\nmode={mode}\n")


def _stub_axle_noop() -> str:
    """Freeze tip/site apply so rematerialize polarity is observable alone."""
    assert AXLE.is_file(), "seating desk missing axle helper"
    original = AXLE.read_text()
    AXLE.write_text("#!/bin/bash\ntrue\n")
    return original


def _restore_axle(original: str) -> None:
    AXLE.write_text(original)


def _seat_with_axle_frozen() -> None:
    REPORT.unlink(missing_ok=True)
    proc = subprocess.run(
        ["/bin/bash", "/app/ops/run_dhcp_seat.sh"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"seat failed: {proc.stderr}\n{proc.stdout}"


def test_q3_topaz():
    """Ledger schema, schema_tag, and seat_ok after seating."""
    doc = _reseat()
    assert doc["schema_tag"] == "dhcp-seat-v1"
    assert isinstance(doc["subnets"], list)
    assert isinstance(doc["reservations"], list)
    assert isinstance(doc["conflicts"], list)
    assert isinstance(doc["seat_ok"], bool)
    assert doc["seat_ok"]
    for row in doc["subnets"]:
        assert {"id", "pool", "generation"} <= set(row)
        assert isinstance(row["id"], int)
        assert isinstance(row["generation"], int)
    for row in doc["reservations"]:
        assert {"hw", "ip", "subnet", "honored"} <= set(row)
        assert isinstance(row["honored"], bool)
        assert isinstance(row["subnet"], int)
    for row in doc["conflicts"]:
        assert {"ip", "reason"} <= set(row)
        assert row["reason"] in {
            "duplicate_ip",
            "lease_collision",
            "generation_floor",
            "pool_miss",
            "shadowed",
        }


def test_n4_beryl():
    """Two seating runs leave byte-identical ledger bytes."""
    _reseat()
    first = REPORT.read_bytes()
    _reseat()
    second = REPORT.read_bytes()
    assert first == second
    assert first.endswith(b"\n")


def test_w7_quartz():
    """Frozen fixtures match verifier-owned digests (not agent packaging pin)."""
    assert VERIFIER_PIN.is_file()
    lookup = {
        "subnet_10.toml": DATA_KEA / "subnet_10.toml",
        "subnet_20.toml": DATA_KEA / "subnet_20.toml",
        "subnet_30.toml": DATA_KEA / "subnet_30.toml",
        "10-core.conf": SEED_D / "10-core.conf",
        "40-lab.conf": SEED_D / "40-lab.conf",
        "site_standard.conf": SITE,
    }
    expected = {}
    for line in VERIFIER_PIN.read_text().splitlines():
        if not line.strip():
            continue
        digest, path = line.split(None, 1)
        expected[Path(path).name] = digest
    assert expected, "empty verifier pin"
    for name, digest in expected.items():
        got = _file_sha256(lookup[name])
        assert got == digest, f"fixture drift on {name}"


def test_j2_onyx():
    """Folded site-standard tokens survive cutover into live 90-local."""
    _reseat()
    live = _parse_kv((ETC / "kea-dhcp4.d" / "90-local.conf").read_text())
    site = _parse_kv(SITE.read_text())
    assert live.get("tip_policy") == site.get("tip_policy")
    assert live.get("bind_order") == site.get("bind_order")
    assert live.get("tip_policy") == "site_standard"
    for k, v in site.items():
        if k.startswith("reserve."):
            assert live.get(k) == v


def test_v5_coral():
    """Subnet generations are sealed journal tips; floor polarity visible."""
    doc = _reseat()
    tips = _journal_tips()
    by_id = {r["id"]: r for r in doc["subnets"]}
    for sid, gen in tips.items():
        assert by_id[int(sid)]["generation"] == gen
    floors = _floors()
    below = [sid for sid, gen in tips.items() if gen < floors[sid]]
    above = [sid for sid, gen in tips.items() if gen >= floors[sid]]
    assert below, "fixture must expose a below-floor subnet"
    assert above, "fixture must expose an above-floor subnet"
    assert (VAR / "state" / "gen.live").read_text().strip() == (
        VAR / "state" / "gen.target"
    ).read_text().strip()


def test_p9_jade():
    """Active memfile lease blocks honor for a colliding reservation."""
    doc = _reseat()
    leases = _active_leases()
    assert leases, "fixture must expose active memfile rows"
    collided = False
    for r in doc["reservations"]:
        if r["ip"] in leases and leases[r["ip"]] != r["hw"].lower():
            assert not r["honored"]
            assert any(
                c["ip"] == r["ip"] and c["reason"] == "lease_collision"
                for c in doc["conflicts"]
            )
            collided = True
    assert collided
    expired_ips = set()
    for i, line in enumerate((VAR / "ops" / "memfile.csv").read_text().splitlines()):
        if i == 0 and line.lower().startswith("ip,"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3 and parts[2].lower() == "expired":
            expired_ips.add(parts[0])
    for ip in expired_ips:
        assert not any(
            c["ip"] == ip and c["reason"] == "lease_collision" for c in doc["conflicts"]
        )


def test_h8_amber():
    """Abort package stays forensic; live drop-in is site-standard."""
    _reseat()
    abort_kv = _parse_kv((VAR / "ops" / "abort.d" / "90-local.conf").read_text())
    live_kv = _parse_kv((ETC / "kea-dhcp4.d" / "90-local.conf").read_text())
    site = _parse_kv(SITE.read_text())
    assert abort_kv.get("tip_policy") == "prefer_abort"
    site_reserve_keys = [k for k in site if k.startswith("reserve.")]
    assert site_reserve_keys
    sample = site_reserve_keys[-1]
    assert abort_kv.get(sample) != live_kv.get(sample)
    assert live_kv.get("tip_policy") == site.get("tip_policy")
    assert live_kv.get(sample) == site.get(sample)


def test_c1_flint():
    """Matching cutover.ok skips rematerialize across a frozen tip-apply seat."""
    _reseat()
    receipt = VAR / "state" / "cutover.ok"
    assert receipt.is_file()
    rkv = _parse_kv(receipt.read_text())
    target = (VAR / "state" / "gen.target").read_text().strip()
    assert rkv.get("gen") == target
    assert rkv.get("mode") == "seal"
    live = ETC / "kea-dhcp4.d" / "90-local.conf"
    assert live.is_file()
    assert live.stat().st_size > 0
    site_before = live.read_text()
    original = _stub_axle_noop()
    try:
        _seat_with_axle_frozen()
        assert (ETC / "kea-dhcp4.d" / "90-local.conf").read_text() == site_before
        assert _parse_kv(site_before).get("tip_policy") == "site_standard"
    finally:
        _restore_axle(original)


def test_c2_agate():
    """Wrong-gen cutover.ok rematerializes abort when tip-apply is frozen."""
    _reseat()
    target = (VAR / "state" / "gen.target").read_text().strip()
    _write_receipt(str(int(target) + 99), "seal")
    original = _stub_axle_noop()
    try:
        _seat_with_axle_frozen()
        live_kv = _parse_kv((ETC / "kea-dhcp4.d" / "90-local.conf").read_text())
        abort_kv = _parse_kv((VAR / "ops" / "abort.d" / "90-local.conf").read_text())
        assert live_kv.get("tip_policy") == abort_kv.get("tip_policy")
        assert live_kv.get("tip_policy") == "prefer_abort"
    finally:
        _restore_axle(original)
        _reseat()


def test_c3_spinel():
    """Wrong-mode cutover.ok rematerializes abort when tip-apply is frozen."""
    _reseat()
    target = (VAR / "state" / "gen.target").read_text().strip()
    _write_receipt(target, "draft")
    original = _stub_axle_noop()
    try:
        _seat_with_axle_frozen()
        live_kv = _parse_kv((ETC / "kea-dhcp4.d" / "90-local.conf").read_text())
        assert live_kv.get("tip_policy") == "prefer_abort"
    finally:
        _restore_axle(original)
        _reseat()


def test_r6_slate():
    """Durable prefer selects durable pools, not live decoys."""
    doc = _reseat()
    prefer = _parse_kv((VAR / "ops" / "prefer.toml").read_text())
    assert prefer.get("pool_root") == "durable"
    pools = _durable_pools()
    by_id = {r["id"]: r for r in doc["subnets"]}
    for sid, cidr in pools.items():
        assert by_id[int(sid)]["pool"] == cidr
    sample_sid = _roster()[0]
    live_decoy = (ETC / "pools" / f"{sample_sid}.pool").read_text().strip()
    assert by_id[int(sample_sid)]["pool"] != live_decoy


def test_u2_mica():
    """Ledger matches sealed verifier ledger as unordered row multisets."""
    doc = _reseat()
    exp = _sealed()
    assert doc["seat_ok"]
    assert doc["schema_tag"] == exp["schema_tag"]
    assert _subnet_rows(doc) == _subnet_rows(exp)
    assert _reservation_rows(doc) == _reservation_rows(exp)
    assert _conflict_rows(doc) == _conflict_rows(exp)


def test_m1_opal():
    """Honor polarity vs sealed ledger: mixed honored/denied and floor denial."""
    doc = _reseat()
    exp = _sealed()
    assert _reservation_rows(doc) == _reservation_rows(exp)
    assert any(r["honored"] for r in doc["reservations"])
    assert any(not r["honored"] for r in doc["reservations"])
    assert any(c["reason"] == "generation_floor" for c in doc["conflicts"])


def test_k5_garnet():
    """Duplicate IP reservations appear once in conflicts and are never honored."""
    doc = _reseat()
    counts: dict[str, int] = {}
    for r in doc["reservations"]:
        counts[r["ip"]] = counts.get(r["ip"], 0) + 1
    dups = [ip for ip, n in counts.items() if n > 1]
    assert dups, "fixture must expose a duplicate reservation IP"
    for ip in dups:
        rows = [r for r in doc["reservations"] if r["ip"] == ip]
        assert all(not r["honored"] for r in rows)
        dup_conflicts = [c for c in doc["conflicts"] if c["ip"] == ip]
        assert len(dup_conflicts) == 1
        assert dup_conflicts[0]["reason"] == "duplicate_ip"


def test_s8_zircon():
    """Live conf.d shadow of the same hw emits shadowed conflict on prior IP."""
    doc = _reseat()
    shadowed = _fold_live_shadows()
    assert shadowed, "live fold must expose a shadowed prior IP"
    for ip in shadowed:
        assert any(
            c["ip"] == ip and c["reason"] == "shadowed" for c in doc["conflicts"]
        )
    by_hw = {r["hw"]: r for r in doc["reservations"]}
    live_files = sorted((ETC / "kea-dhcp4.d").glob("*.conf"))
    assert live_files
    last_kv = _parse_kv(live_files[-1].read_text())
    first_kv = _parse_kv(live_files[0].read_text())
    for k, early in first_kv.items():
        if not k.startswith("reserve."):
            continue
        late = last_kv.get(k)
        if not late or late == early:
            continue
        hw = k[len("reserve.") :]
        early_ip = early.split(":", 1)[0]
        late_ip = late.split(":", 1)[0]
        assert early_ip in shadowed
        assert by_hw[hw]["ip"] == late_ip
        assert by_hw[hw]["honored"]


def test_t4_pearl():
    """Surface keahealth may look fine while deep seating is graded."""
    doc = _reseat()
    assert doc["seat_ok"]
    proc = subprocess.run(
        ["/usr/local/bin/keahealth"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "OK"
