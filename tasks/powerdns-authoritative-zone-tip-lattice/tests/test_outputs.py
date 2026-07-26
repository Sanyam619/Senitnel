"""Verifier for PowerDNS authoritative zone tip seating.

Re-enters /app/ops/run_pdns_seat.sh and derives EXPECTED seating from
durable fixtures under /var/lib/powerdns and /app/data — never from the
agent report alone. Durable inputs are pinned by sha256 in
tests/ledgers/pins.sha256.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/pdns-seat.json")
ETC = Path("/etc/powerdns")
VAR = Path("/var/lib/powerdns")
OPS = VAR / "ops"
STATE = VAR / "state"
SITE = Path("/app/config/site_standard.conf")
ENTRY = "/app/ops/run_pdns_seat.sh"
PINS = Path(__file__).parent / "ledgers" / "pins.sha256"
ALLOWED_PREF = {"durable", "authority"}


def _seat() -> dict:
    proc = subprocess.run(
        [ENTRY], capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, (proc.stdout + proc.stderr)[-2000:]
    return json.loads(REPORT.read_text())


def _seat_bytes() -> bytes:
    _seat()
    return REPORT.read_bytes()



def _durable(report: dict) -> bool:
    return bool(report["seat_ok"])


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
    path = ETC / "zone.roster"
    return [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]


def _target() -> str:
    return (STATE / "gen.target").read_text().strip()


def _resolve_tip() -> dict[str, dict]:
    target = _target()
    chosen = None
    seal_ok = False
    for line in (OPS / "zone_journal.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") == "seal" and str(row.get("gen")) == target:
            seal_ok = True
        if row.get("tag") != "batch" or str(row.get("gen")) != target:
            continue
        if row.get("sealed") is True and row.get("complete") is True:
            chosen = row
    assert seal_ok, "zone journal missing seal for gen.target"
    assert chosen is not None, "no sealed complete batch for gen.target"
    return {
        z["name"]: {"serial": int(z["serial"]), "records": z.get("records", [])}
        for z in chosen["zones"]
    }


def _retired() -> set[str]:
    out: set[str] = set()
    for line in (OPS / "retired_stores.jsonl").read_text().splitlines():
        if line.strip():
            out.add(str(json.loads(line).get("store", "")))
    return out


def _store_sel() -> str:
    retired = _retired()
    best_epoch = -1
    best = ""
    for line in (OPS / "store_registry.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("tag") != "bind":
            continue
        if str(row.get("store", "")) in retired:
            continue
        if int(row.get("epoch", -1)) > best_epoch:
            best_epoch = int(row.get("epoch", -1))
            best = str(row["store"])
    assert best, "no eligible store binding"
    return best


def _abort_set() -> set[str]:
    aborts: set[str] = set()
    for path in sorted((ETC / "pdns.d").glob("*.conf")):
        for raw in path.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line.startswith("abort-zone="):
                continue
            val = line.split("=", 1)[1].strip()
            if val:
                aborts.add(val)
    return aborts


def _holds() -> dict[tuple[str, str, str], str]:
    out: dict[tuple[str, str, str], str] = {}
    for line in (OPS / "holds.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[(row["zone"], row["name"], row["type"])] = row["content"]
    return out


def _floor(name: str) -> int:
    return int((VAR / "floors" / f"{name}.floor").read_text().strip())


def _ns(name: str) -> str:
    return (VAR / "zones" / f"{name}.ns").read_text().strip()


def _expected() -> tuple[list[dict], list[dict]]:
    tips = _resolve_tip()
    target = int(_target())
    sel = _store_sel()
    aborted = _abort_set()
    holds = _holds()
    zones: list[dict] = []
    records: list[dict] = []
    for name in _roster():
        tip = tips[name]
        published = (
            tip["serial"] > 0
            and target >= _floor(name)
            and name not in aborted
        )
        zones.append(
            {
                "name": name,
                "serial": tip["serial"],
                "backend": sel,
                "generation": target,
                "published": published,
            }
        )
        for row in tip["records"]:
            held = holds.get((name, row["name"], row["type"]))
            content = held if held is not None else row["content"]
            records.append(
                {
                    "zone": name,
                    "name": row["name"],
                    "type": row["type"],
                    "content": content,
                    "honored": content == row["content"],
                }
            )
    return zones, records


def test_c2_agate():
    """Report schema: tag literal, roster-ordered zones, typed fields, non-empty records ledger."""
    report = _seat()
    assert report["schema_tag"] == "pdns-seat-v1"
    assert isinstance(report["seat_ok"], bool)
    roster = _roster()
    zones = report["zones"]
    assert [z["name"] for z in zones] == roster
    for z in zones:
        assert isinstance(z["serial"], int)
        assert isinstance(z["backend"], str)
        assert isinstance(z["generation"], int)
        assert isinstance(z["published"], bool)
    records = report["records"]
    assert records, "records ledger is empty"
    for r in records:
        assert r["zone"] in roster
        assert isinstance(r["name"], str)
        assert isinstance(r["type"], str)
        assert isinstance(r["content"], str)
        assert isinstance(r["honored"], bool)


def test_d7_slate():
    """Durable inputs match the pinned sha256 ledger and the seat reports seat_ok true."""
    proc = subprocess.run(
        ["sha256sum", "--check", "--strict", str(PINS)],
        capture_output=True,
        text=True,
        check=False,
        cwd="/",
    )
    assert proc.returncode == 0, (
        "durable input drifted:\n" + proc.stdout + proc.stderr
    )
    report = _seat()
    assert _durable(report)


def test_k4_basalt():
    """Applied tips equal the journal-resolved batch; superseded and incomplete batches rejected; tip state records match."""
    report = _seat()
    tips = _resolve_tip()
    target = int(_target())
    for z in report["zones"]:
        name = z["name"]
        assert z["serial"] == tips[name]["serial"], name
        assert z["generation"] == target, name
        state_serial = int((STATE / f"tip_{name}.serial").read_text().strip())
        state_gen = int((STATE / f"tip_{name}.gen").read_text().strip())
        assert state_serial == tips[name]["serial"], name
        assert state_gen == target, name
        state_rows = json.loads((STATE / f"tip_{name}.records").read_text())
        assert state_rows == tips[name]["records"], name
    by_name = {z["name"]: z for z in report["zones"]}
    assert by_name["crest.example"]["serial"] != 2026071901, (
        "superseded gen revision applied"
    )
    assert all(z["generation"] != 9 for z in report["zones"]), (
        "incomplete later batch applied"
    )
    assert (STATE / "gen.live").read_text().strip() == _target()


def test_r8_garnet():
    """Backend is the highest-epoch non-retired store binding across report, state, and live sheets."""
    report = _seat()
    sel = _store_sel()
    retired = _retired()
    assert sel not in retired
    assert (STATE / "store.sel").read_text().strip() == sel
    for z in report["zones"]:
        assert z["backend"] == sel, z["name"]
        assert z["backend"] not in retired, z["name"]
        sheet = (ETC / "zones.d" / f'{z["name"]}.store').read_text().strip()
        assert sheet == sel, z["name"]
        live_serial = (
            (ETC / "serials" / f'{z["name"]}.serial').read_text().strip()
        )
        assert live_serial == str(z["serial"]), z["name"]


def test_m1_jasper():
    """Publish matrix equals the recomputed durable verdict with mixed polarity; folded abort zones stay unpublished."""
    report = _seat()
    expected_zones, _ = _expected()
    got = {z["name"]: z["published"] for z in report["zones"]}
    want = {z["name"]: z["published"] for z in expected_zones}
    assert got == want
    flags = set(want.values())
    assert flags == {True, False}, "publish matrix lost mixed polarity"
    aborted = _abort_set()
    assert aborted, "fold abort set is empty"
    for name in aborted:
        if name in got:
            assert got[name] is False, name


def test_v6_topaz():
    """Record ledger equals the recomputed hold/tip verdict and matches live record sheets."""
    report = _seat()
    _, expected_records = _expected()
    assert report["records"] == expected_records
    honored = [r["honored"] for r in report["records"]]
    assert True in honored and False in honored, (
        "honor ledger lost mixed polarity"
    )
    for r in report["records"]:
        sheet = (ETC / "zones.d" / f'{r["zone"]}.rec').read_text()
        assert f'{r["name"]} {r["type"]} {r["content"]}' in sheet, r


def test_h3_onyx():
    """Live 90-local carries site-standard tokens, abort package stays forensic, receipt is plain key=value at gen.target."""
    _seat()
    live = _parse_kv((ETC / "pdns.d" / "90-local.conf").read_text())
    site = _parse_kv(SITE.read_text())
    for k, v in site.items():
        assert live.get(k) == v, f"site token missing: {k}"
    assert live.get("zone_policy") != "prefer_abort"
    pkg = _parse_kv((OPS / "abort.d" / "90-local.conf").read_text())
    assert pkg.get("zone_policy") == "prefer_abort", (
        "abort package no longer forensic"
    )
    receipt_path = STATE / "cutover.ok"
    assert receipt_path.is_file()
    raw = receipt_path.read_text()
    assert "{" not in raw, "receipt must be plain key=value"
    receipt = _parse_kv(raw)
    assert receipt.get("gen") == _target()
    assert receipt.get("mode") == "seal"


def test_p9_beryl():
    """Preference settled durable/authority, tip bind acceptance and gen.live match gen.target."""
    _seat()
    pref = _parse_kv((OPS / "prefer.toml").read_text())
    mode = pref.get("mode", "").strip('"')
    assert mode in ALLOWED_PREF, f"preference mode {mode!r}"
    bind = _parse_kv((OPS / "tip_bind.accept").read_text())
    assert bind.get("gen") == _target(), "tip bind acceptance stale"
    assert (STATE / "gen.live").read_text().strip() == _target()


def test_w5_quartz():
    """Surface bait absent: no surface serials, generations, probe rows, or lab addresses in the seat."""
    report = _seat()
    surface_serials = set()
    for path in (VAR / "surface" / "tips").glob("tip_*.serial"):
        surface_serials.add(int(path.read_text().strip()))
    target = int(_target())
    for z in report["zones"]:
        assert z["serial"] not in surface_serials, z["name"]
        assert z["generation"] == target and z["generation"] != 1, z["name"]
    for r in report["records"]:
        assert not r["content"].startswith("10.0.0."), r
    for name in _roster():
        sheet = (ETC / "zones.d" / f"{name}.rec").read_text()
        assert "v=trace" not in sheet, name
        assert "10.0.0." not in sheet, name


def test_a4_apex():
    """Live record sheets open with the durable apex NS line; apex lines stay out of the records ledger."""
    report = _seat()
    for name in _roster():
        lines = (ETC / "zones.d" / f"{name}.rec").read_text().splitlines()
        assert lines, name
        assert lines[0] == f"@ NS {_ns(name)}", name
    for r in report["records"]:
        assert r["name"] != "@"
        assert r["type"] != "NS"


def test_x2_flint():
    """Two seating passes leave byte-identical report and record sheets."""
    first = _seat_bytes()
    sheets_first = {
        name: (ETC / "zones.d" / f"{name}.rec").read_bytes()
        for name in _roster()
    }
    second = _seat_bytes()
    assert first == second, "report not byte-identical across seats"
    for name in _roster():
        again = (ETC / "zones.d" / f"{name}.rec").read_bytes()
        assert again == sheets_first[name], name
    assert _durable(json.loads(second)), (
        "stable reports only count on a durable seat"
    )


def test_b8_coral():
    """Seating re-entry regenerates the report after /output is wiped."""
    REPORT.unlink(missing_ok=True)
    report = _seat()
    assert REPORT.is_file()
    assert _durable(report)


def test_g6_umber():
    """Abort residue plus a removed receipt recovers to the baseline seat on re-entry."""
    baseline = _seat_bytes()
    live = ETC / "pdns.d" / "90-local.conf"
    live.write_bytes((OPS / "abort.d" / "90-local.conf").read_bytes())
    (STATE / "cutover.ok").unlink(missing_ok=True)
    after = _seat_bytes()
    assert after == baseline, "seat did not recover from abort residue"
    kv = _parse_kv(live.read_text())
    assert kv.get("zone_policy") != "prefer_abort"
    receipt = _parse_kv((STATE / "cutover.ok").read_text())
    assert receipt.get("gen") == _target()
    assert receipt.get("mode") == "seal"


def test_s1_pyrite():
    """Live preference degrades the seat while pdnshealth still prints serving; durable preference recovers baseline."""
    baseline = _seat_bytes()
    pref_path = OPS / "prefer.toml"
    saved = pref_path.read_bytes()
    try:
        pref_path.write_text('mode = "live"\ntag_path = "surface"\n')
        report = _seat()
        assert not _durable(report), (
            "live preference must not report a durable seat"
        )
        health = subprocess.run(
            ["/usr/local/bin/pdnshealth"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert health.returncode == 0
        assert health.stdout.strip() == "serving", (
            "surface health must keep serving while the seat is degraded"
        )
        surf = int(
            (VAR / "surface" / "tips" / "tip_crest.example.serial")
            .read_text()
            .strip()
        )
        applied = int((STATE / "tip_crest.example.serial").read_text().strip())
        assert applied == surf, "surface tips did not rematerialize"
    finally:
        pref_path.write_bytes(saved)
    recovered = _seat_bytes()
    assert recovered == baseline, "durable preference did not recover"
    assert _durable(json.loads(recovered)), (
        "recovery must land on a durable seat"
    )


def test_t4_amber():
    """Novel sealed generation-8 batch injection re-seats to the new tips and flips the floor-8 zone."""
    baseline = _seat_bytes()
    journal = OPS / "zone_journal.jsonl"
    gen_target = STATE / "gen.target"
    saved_journal = journal.read_bytes()
    saved_target = gen_target.read_bytes()
    inject_serials = {
        "crest.example": 2026090801,
        "harbor.example": 2026090802,
        "mesa.example": 2026090803,
        "quarry.example": 2026090804,
        "tundra.example": 2026090805,
    }
    batch = {
        "tag": "batch",
        "gen": 8,
        "sealed": True,
        "complete": True,
        "zones": [
            {
                "name": name,
                "serial": serial,
                "records": [
                    {"name": "www", "type": "A", "content": "198.51.100.8"}
                ],
            }
            for name, serial in inject_serials.items()
        ],
    }
    try:
        with journal.open("a") as fh:
            fh.write(json.dumps(batch) + "\n")
            fh.write(json.dumps({"tag": "seal", "gen": 8}) + "\n")
        gen_target.write_text("8\n")
        report = _seat()
        by_name = {z["name"]: z for z in report["zones"]}
        for name, serial in inject_serials.items():
            assert by_name[name]["serial"] == serial, name
            assert by_name[name]["generation"] == 8, name
        assert by_name["mesa.example"]["published"] is True, (
            "floor-8 zone must publish at generation 8"
        )
        aborted = _abort_set()
        for name in aborted:
            if name in by_name:
                assert by_name[name]["published"] is False, name
        assert _durable(report)
    finally:
        journal.write_bytes(saved_journal)
        gen_target.write_bytes(saved_target)
    recovered = _seat_bytes()
    assert recovered == baseline


def test_n3_opal():
    """Novel hold injection pins live content and flips honored; removing it recovers baseline."""
    baseline = _seat_bytes()
    holds_path = OPS / "holds.jsonl"
    saved = holds_path.read_bytes()
    inject = {
        "zone": "crest.example",
        "name": "www",
        "type": "A",
        "content": "192.0.2.77",
    }
    try:
        with holds_path.open("a") as fh:
            fh.write(json.dumps(inject) + "\n")
        report = _seat()
        rows = [
            r
            for r in report["records"]
            if r["zone"] == "crest.example"
            and r["name"] == "www"
            and r["type"] == "A"
        ]
        assert len(rows) == 1
        assert rows[0]["content"] == "192.0.2.77"
        assert rows[0]["honored"] is False
        assert _durable(report)
    finally:
        holds_path.write_bytes(saved)
    recovered = _seat_bytes()
    assert recovered == baseline
