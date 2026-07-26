"""Behavioral checks for the admission quarantine ledger."""

import json
import subprocess
import tempfile
from pathlib import Path

APP = Path("/app")
LEDGER = Path("/output/admit-ledger.json")
QUAR = Path("/output/quarantine.json")
RUNTIME = APP / "data" / "state" / "runtime.json"
SCEN_DIR = APP / "data" / "scenarios"
JOURNAL = APP / "data" / "seating" / "canon.journal"
DURABLE = APP / "data" / "roots" / "durable.map"
SURFCHECK_SCRIPT = APP / "scripts" / "surfcheck"
RUN_ADMIT_SCRIPT = APP / "scripts" / "run-admit.sh"
FRAMECHECK = Path("/app/bin/framecheck")

RUN_ADMIT = "/app/scripts/run-admit.sh"
MESH_REFRESH = "/app/scripts/mesh-refresh.sh"
SURFCHECK = "/app/bin/surfcheck"

EXPECTED = {
    "m2": ("job-m2", "accept", "ok_admit"),
    "w2": ("job-w2", "accept", "ok_admit"),
    "k9": ("job-k9", "quarantine", "path_drift"),
    "n4": ("job-n4", "quarantine", "fd_stale"),
    "p7": ("job-p7", "quarantine", "notify_skew"),
    "q3": ("job-q3", "quarantine", "epoch_revoke"),
    "r6": ("job-r6", "accept", "ok_admit"),
    "t1": ("job-t1", "accept", "ok_admit"),
    "u8": ("job-u8", "accept", "ok_admit"),
    "v5": ("job-v5", "accept", "ok_admit"),
    "x2": ("job-x2", "accept", "ok_admit"),
    "h4": ("job-h4", "quarantine", "path_drift"),
    "s9": ("job-s9", "quarantine", "replay"),
}

_FORBIDDEN_SNAP = None


def _journal_map():
    """Agent-visible seating authority — same source tests and solvers use."""
    out = {}
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        alias = row["alias"]
        if "canon" in row:
            out[alias] = row["canon"]
        elif "via" in row:
            out[alias] = row["via"]
    return out


def _materialize_durable_from_journal():
    m = _journal_map()
    lines = ["# durable seating recovered from sealed seating journal"]
    for k in sorted(m):
        lines.append(f"{k}={m[k]}")
    return "\n".join(lines) + "\n"


def _durable_pairs(text):
    """Parse durable.map into alias=target pairs, ignoring comments/blank lines."""
    pairs = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        alias, target = line.split("=", 1)
        pairs[alias.strip()] = target.strip()
    return pairs


def _snapshot_bytes(path):
    return path.read_bytes()


def _snapshot_tree(root):
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(APP))] = path.read_bytes()
    return out


def _forbidden_snap():
    global _FORBIDDEN_SNAP
    if _FORBIDDEN_SNAP is None:
        _FORBIDDEN_SNAP = (
            _snapshot_tree(SCEN_DIR),
            _snapshot_bytes(SURFCHECK_SCRIPT),
            _snapshot_bytes(RUN_ADMIT_SCRIPT),
            _snapshot_bytes(FRAMECHECK),
            _snapshot_bytes(JOURNAL),
        )
    return _FORBIDDEN_SNAP


def _assert_prohibited_untouched():
    scenarios, surf, run_bytes, gate, journal = _forbidden_snap()
    assert _snapshot_tree(SCEN_DIR) == scenarios
    assert _snapshot_bytes(SURFCHECK_SCRIPT) == surf
    assert _snapshot_bytes(RUN_ADMIT_SCRIPT) == run_bytes
    assert _snapshot_bytes(FRAMECHECK) == gate
    assert _snapshot_bytes(JOURNAL) == journal


def _reset_runtime():
    RUNTIME.write_text('{"epoch": 7}\n')


def _restore_durable():
    DURABLE.write_text(_materialize_durable_from_journal())


def _run_admit():
    _restore_durable()
    _reset_runtime()
    subprocess.run(
        [RUN_ADMIT],
        check=True,
        cwd="/app",
        capture_output=True,
    )
    _assert_prohibited_untouched()
    return _load()


def _load():
    return json.loads(LEDGER.read_text())


def _cases(data):
    return {c["id"]: c for c in data["cases"]}


def _runtime_epoch():
    return json.loads(RUNTIME.read_text())["epoch"]


def _assert_row(data, scenario_id):
    row = _cases(data)[scenario_id]
    job_id, decision, reason_code = EXPECTED[scenario_id]
    assert row["job_id"] == job_id
    assert row["decision"] == decision
    assert row["reason_code"] == reason_code


def _surf_lines():
    proc = subprocess.run(
        [SURFCHECK],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = {}
    for line in proc.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            lines[parts[0]] = parts[1]
    return lines


def test_m8_obsidian():
    """Accept case w2 under durable seating and notify integrity."""
    data = _run_admit()
    _assert_row(data, "w2")


def test_k3_garnet():
    """Alias k9 quarantines for path_drift once seating journal is authoritative."""
    data = _run_admit()
    _assert_row(data, "k9")
    assert _cases(data)["k9"]["reason_code"] != "ok_admit"


def test_n4_topaz():
    """Stale-fd case n4 quarantines as fd_stale, not path_drift."""
    data = _run_admit()
    _assert_row(data, "n4")
    assert _cases(data)["n4"]["reason_code"] != "path_drift"


def test_p7_onyx():
    """Notify integrity miss p7 quarantines with notify_skew."""
    data = _run_admit()
    _assert_row(data, "p7")
    assert _cases(data)["p7"]["decision"] == "quarantine"


def test_q7_amber():
    """Revoke-band case q3 quarantines as epoch_revoke, not notify_skew."""
    data = _run_admit()
    _assert_row(data, "q3")
    assert _cases(data)["q3"]["reason_code"] != "notify_skew"


def test_r1_zircon():
    """Mesh refresh must not replace journal-resolved durable tip with live bait."""
    d1 = _run_admit()
    assert d1["schema_version"] == "admit-mesh-1"
    assert d1["reload_epoch"] == 7
    assert _runtime_epoch() == 7
    assert _durable_pairs(DURABLE.read_text()) == _durable_pairs(
        _materialize_durable_from_journal()
    )
    m1 = {c["id"]: (c["decision"], c["reason_code"]) for c in d1["cases"]}
    durable_before = DURABLE.read_bytes()

    subprocess.run(
        [MESH_REFRESH],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [RUN_ADMIT],
        check=True,
        cwd="/app",
        capture_output=True,
    )
    _assert_prohibited_untouched()
    d2 = _load()
    m2 = {c["id"]: (c["decision"], c["reason_code"]) for c in d2["cases"]}
    assert m1 == m2
    assert d2["reload_epoch"] == d1["reload_epoch"] == 7
    assert _runtime_epoch() == 7
    assert DURABLE.read_bytes() == durable_before
    assert _durable_pairs(DURABLE.read_text()) == _durable_pairs(
        _materialize_durable_from_journal()
    )
    for sid in EXPECTED:
        _assert_row(d2, sid)


def test_t6_jade():
    """Surface skim OK on k9 while host admission still quarantines path_drift."""
    data = _run_admit()
    _assert_row(data, "t1")
    _assert_row(data, "k9")
    surf = _surf_lines()
    assert surf.get("k9") == "OK"
    assert _cases(data)["k9"]["decision"] == "quarantine"


def test_u2_quartz():
    """Accept u8 after correct notify material/fold (not notify_skew)."""
    data = _run_admit()
    _assert_row(data, "u8")
    assert _cases(data)["u8"]["reason_code"] != "notify_skew"


def test_v5_spinel():
    """Journal multi-hop seating resolves v5 into vault and admits."""
    data = _run_admit()
    _assert_row(data, "v5")
    jm = _journal_map()
    alias = "/data/alias/v5/blob"
    assert alias in jm
    mid = jm[alias]
    assert mid in jm
    assert jm[mid].startswith("/data/vault/")


def test_x2_beryl():
    """Accept x2 under correct notify check (not fd_stale)."""
    data = _run_admit()
    _assert_row(data, "x2")
    assert _cases(data)["x2"]["reason_code"] != "fd_stale"


def test_h6_jadeite():
    """Outside alias h4 quarantines path_drift, not notify_skew."""
    data = _run_admit()
    _assert_row(data, "h4")
    assert _cases(data)["h4"]["reason_code"] != "notify_skew"


def test_w9_coral():
    """In-band r6 accepts (ok_admit) rather than epoch_revoke."""
    data = _run_admit()
    _assert_row(data, "r6")
    assert _cases(data)["r6"]["reason_code"] != "epoch_revoke"


def test_y4_opal():
    """Full matrix: surface false-green, accepts, path_drift, and replay quarantine."""
    data = _run_admit()
    assert data["schema_version"] == "admit-mesh-1"
    surf = _surf_lines()
    assert surf.get("k9") == "OK"
    assert surf.get("h4") == "OK"
    assert _cases(data)["k9"]["decision"] == "quarantine"
    assert _cases(data)["h4"]["decision"] == "quarantine"
    assert _cases(data)["m2"]["decision"] == "accept"
    assert _cases(data)["s9"]["reason_code"] == "replay"
    q = json.loads(QUAR.read_text())
    assert q["version"] == 1
    reasons = {r["reason"] for r in q["rows"]}
    assert "replay" in reasons
    assert "path_drift" in reasons


def test_z2_fluorite():
    """Rebuild from /app then re-admit; durable preference must keep notify bodies."""
    _restore_durable()
    _reset_runtime()
    mat_path = APP / "rz" / "mat_q.c"
    good = mat_path.read_bytes()
    stub = (APP / "data" / "surface" / "stubs_mat_q.c").read_bytes()
    assert good != stub
    subprocess.run(["make"], check=True, cwd="/app", capture_output=True)
    assert mat_path.read_bytes() == good
    subprocess.run(
        [RUN_ADMIT],
        check=True,
        cwd="/app",
        capture_output=True,
    )
    _assert_prohibited_untouched()
    data = _load()
    for sid in EXPECTED:
        _assert_row(data, sid)


def test_a1_framecheck():
    """Sealed framecheck accepts a known-good notify frame (schedule pin)."""
    seed = json.loads((APP / "data/fixtures/seed.json").read_text())["seed_hex"]
    scen = json.loads((SCEN_DIR / "m2.json").read_text())
    frame = {
        "seed_hex": seed,
        "epoch": scen["epoch"],
        "lane": scen["lane"],
        "strand": 61,
        "payload_hex": scen["payload_hex"],
        "check": scen["check"],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        fh.write(json.dumps(frame))
        frame_path = fh.name
    proc = subprocess.run(
        ["/app/bin/framecheck", "--frame", frame_path],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "ok" in proc.stdout


def test_b2_journal_authority():
    """Seating journal maps k9 outside vault; host decision follows journal."""
    jm = _journal_map()
    assert jm["/data/alias/k9/blob"].startswith("/data/outside/")
    data = _run_admit()
    _assert_row(data, "k9")


def test_c3_durable_tip_journal():
    """Durable tip after admit matches sealed seating journal resolution."""
    data = _run_admit()
    assert _durable_pairs(DURABLE.read_text()) == _durable_pairs(
        _materialize_durable_from_journal()
    )
    _assert_row(data, "m2")
    _assert_row(data, "v5")
    _assert_row(data, "k9")
