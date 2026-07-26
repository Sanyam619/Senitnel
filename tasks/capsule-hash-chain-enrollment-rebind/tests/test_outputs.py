"""Behavioral checks for the capsule enrollment ledger.

Each test regenerates the ledger from the currently built tools by invoking the
shipped entrypoint, then asserts domain-correct decisions and reason codes. The
expected outcomes live here, not in any environment file.
"""

import json
import subprocess
from pathlib import Path

APP = Path("/app")
LEDGER = Path("/output/enroll-ledger.json")
RUNTIME = APP / "data" / "state" / "runtime.json"
LIVE = APP / "data" / "roots" / "live.bundle"
SCEN_DIR = APP / "data" / "scenarios"
SURFCHECK_SCRIPT = APP / "scripts" / "surfcheck"
RUN_ENROLL_SCRIPT = APP / "scripts" / "run-enroll.sh"

RUN_ENROLL = "/app/scripts/run-enroll.sh"
HOST_RELOAD = "/app/scripts/host-reload.sh"
SURFCHECK = "/app/bin/surfcheck"

# (device_id, decision, reason_code) expected for every scenario.
EXPECTED = {
    "m2": ("dev-a", "accept", "ok_bound"),
    "w2": ("dev-c", "accept", "ok_bound"),
    "q3": ("dev-q", "accept", "ok_bound"),
    "k9": ("dev-k", "reject", "revoked"),
    "n4": ("dev-n", "reject", "stale_chain"),
    "p7": ("dev-b", "reject", "gen_skew"),
    "t1": ("dev-t", "reject", "gen_skew"),
}

_FORBIDDEN_SNAP = None


def _snapshot_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _snapshot_tree(root: Path) -> dict:
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(APP))] = path.read_bytes()
    return out


def _forbidden_snap():
    global _FORBIDDEN_SNAP
    if _FORBIDDEN_SNAP is None:
        _FORBIDDEN_SNAP = {
            "scenarios": _snapshot_tree(SCEN_DIR),
            "surfcheck": _snapshot_bytes(SURFCHECK_SCRIPT),
            "run_enroll": _snapshot_bytes(RUN_ENROLL_SCRIPT),
        }
    return _FORBIDDEN_SNAP


def _assert_prohibited_untouched():
    snap = _forbidden_snap()
    assert _snapshot_tree(SCEN_DIR) == snap["scenarios"]
    assert _snapshot_bytes(SURFCHECK_SCRIPT) == snap["surfcheck"]
    assert _snapshot_bytes(RUN_ENROLL_SCRIPT) == snap["run_enroll"]


def _run_enroll():
    subprocess.run(
        [RUN_ENROLL],
        check=True,
        cwd="/app",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
    device_id, decision, reason_code = EXPECTED[scenario_id]
    assert row["device_id"] == device_id
    assert row["decision"] == decision
    assert row["reason_code"] == reason_code


def _surf_lines():
    proc = subprocess.run(
        [SURFCHECK],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lines = {}
    for line in proc.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            lines[parts[0]] = parts[1]
    return lines


def _assert_green_surf(cap_id):
    surf = _surf_lines()
    assert surf.get(cap_id) == "OK"


def _assert_refuse_not_codes(data, scenario_id, banned):
    row = _cases(data)[scenario_id]
    assert row["decision"] == EXPECTED[scenario_id][1]
    assert row["reason_code"] == EXPECTED[scenario_id][2]
    for code in banned:
        assert row["reason_code"] != code


def _assert_reload_stable():
    d1 = _run_enroll()
    m1 = {c["id"]: (c["decision"], c["reason_code"]) for c in d1["cases"]}
    r1 = d1["reload_epoch"]
    epoch_before = _runtime_epoch()

    backup = LIVE.read_bytes()
    try:
        subprocess.run(
            [HOST_RELOAD],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        d2 = _run_enroll()
    finally:
        LIVE.write_bytes(backup)

    m2 = {c["id"]: (c["decision"], c["reason_code"]) for c in d2["cases"]}
    r2 = d2["reload_epoch"]
    epoch_after = _runtime_epoch()

    assert m1 == m2
    assert r1 == r2
    assert r1 == epoch_before
    assert epoch_before == epoch_after
    for cid in ("m2", "w2", "q3"):
        assert m2[cid] == EXPECTED[cid][1:]


def _assert_schema_and_accepts():
    data = _run_enroll()
    assert data["schema_version"] == "capsule-enroll-1"
    assert data["reload_epoch"] == _runtime_epoch()

    cases = _cases(data)
    assert set(cases.keys()) == set(EXPECTED.keys())
    for row in data["cases"]:
        assert {"id", "device_id", "decision", "reason_code"} <= set(row.keys())
        assert row["decision"] in ("accept", "reject")

    for scenario_id in ("m2", "w2", "q3"):
        _assert_row(data, scenario_id)

    accepts = {cid for cid, row in cases.items() if row["decision"] == "accept"}
    assert {"m2", "w2", "q3"}.issubset(accepts)
    for cid in ("m2", "w2", "q3"):
        assert cases[cid]["reason_code"] == EXPECTED[cid][2]

    surf = _surf_lines()
    assert all(v == "OK" for v in surf.values())
    assert LEDGER.is_file()


def test_m8_obsidian():
    """A sibling whose parent tip does not line up with its device is refused
    for a generation mismatch rather than admitted."""
    data = _run_enroll()
    _assert_row(data, "p7")
    _assert_refuse_not_codes(data, "p7", ("ok_bound", "revoked", "stale_chain"))
    _assert_green_surf("cap_p7")


def test_p7_garnet():
    """The second mismatched sibling is refused for the same reason, proving
    the tip-continuity check is not scenario-specific."""
    data = _run_enroll()
    _assert_row(data, "t1")
    _assert_row(data, "p7")
    _assert_green_surf("cap_t1")


def test_n4_topaz():
    """A record that verified under a prior generation but is now revoked and
    inside the freshness window is refused as a stale chain — not as a hard
    revoke and not as an enroll."""
    data = _run_enroll()
    _assert_row(data, "n4")
    _assert_refuse_not_codes(data, "n4", ("revoked", "ok_bound"))
    _assert_green_surf("cap_n4")


def test_k9_onyx():
    """A revoked record whose claimed generation falls outside the freshness
    window is refused outright — not as stale_chain and not as ok_bound."""
    data = _run_enroll()
    _assert_row(data, "k9")
    _assert_refuse_not_codes(data, "k9", ("stale_chain", "ok_bound"))
    _assert_row(data, "n4")
    _assert_green_surf("cap_k9")


def test_r1_amber():
    """Decisions, reason codes, the ledger reload epoch, and the runtime epoch
    all survive a host reload unchanged."""
    _assert_reload_stable()


def test_t6_zircon():
    """The ledger carries the declared schema and the aligned records enroll,
    while a green surface skim does not by itself grant enrollment."""
    _assert_schema_and_accepts()
