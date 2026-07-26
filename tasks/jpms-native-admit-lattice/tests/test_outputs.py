"""Behavioral checks for JPMS JNI preference lattice admit path.

Each test regenerates the ledger from the currently built tools by invoking the
shipped entrypoint, then asserts domain-correct decisions and reason codes.
Expected outcomes live here, not in any environment file.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

APP = Path("/app")
LEDGER = Path("/output/pack-admit.json")
RUNTIME = APP / "data" / "state" / "runtime.json"
CASES = APP / "data" / "cases"
SURFCHECK_SCRIPT = APP / "bin" / "surfcheck"
RUN_PACK_SCRIPT = APP / "scripts" / "run-pack.sh"

RUN_PACK = "/app/scripts/run-pack.sh"
PACK_RELOAD = "/app/scripts/pack-reload.sh"
PACKHOLD = "/opt/desk/bin/packhold"
SURFCHECK = "/app/bin/surfcheck"

EXPECTED = {
    "q3": ("reject", "bad_layer"),
    "w7": ("reject", "bad_layer"),
    "n2": ("reject", "hook_skew"),
    "k4": ("reject", "stale_reflect"),
    "p9": ("reject", "revoked"),
    "r6": ("accept", "ok_bound"),
    "m1": ("accept", "ok_bound"),
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
        _FORBIDDEN_SNAP = (
            _snapshot_tree(CASES),
            _snapshot_bytes(SURFCHECK_SCRIPT),
            _snapshot_bytes(RUN_PACK_SCRIPT),
        )
    return _FORBIDDEN_SNAP


def _assert_prohibited_untouched():
    snap = _forbidden_snap()
    assert _snapshot_tree(CASES) == snap[0]
    assert _snapshot_bytes(SURFCHECK_SCRIPT) == snap[1]
    assert _snapshot_bytes(RUN_PACK_SCRIPT) == snap[2]


def _run_pack():
    subprocess.run(
        [RUN_PACK],
        check=True,
        cwd="/app",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _assert_prohibited_untouched()
    return _load()


def _load():
    return json.loads(LEDGER.read_text())


def _rows(data):
    return {r["id"]: r for r in data["rows"]}


def _runtime_epoch():
    return json.loads(RUNTIME.read_text())["epoch"]


def _assert_row(data, case_id):
    row = _rows(data)[case_id]
    decision, reason_code = EXPECTED[case_id]
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


def _assert_green_surf(case_id):
    surf = _surf_lines()
    assert surf.get(case_id) == "OK"


def _reinvoke_packhold():
    proc = subprocess.run(
        [PACKHOLD],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.stdout


def test_q3_mica():
    """Wrong JPMS pack must reject as bad_layer even when surfcheck is green."""
    data = _run_pack()
    _assert_green_surf("q3")
    _assert_row(data, "q3")
    hold = _reinvoke_packhold()
    assert "q3 reject bad_layer" in hold


def test_w7_slate():
    """Second wrong-pack generation must also reject as bad_layer via packhold."""
    data = _run_pack()
    _assert_green_surf("w7")
    _assert_row(data, "w7")
    hold = _reinvoke_packhold()
    assert "w7 reject bad_layer" in hold


def test_n2_basalt():
    """Durable vs live root mismatch must reject as hook_skew on re-entry."""
    data = _run_pack()
    _assert_row(data, "n2")
    hold = _reinvoke_packhold()
    assert "n2 reject hook_skew" in hold


def test_k4_flint():
    """In-window revoked material must reject as stale_reflect, not revoked or accept."""
    data = _run_pack()
    _assert_row(data, "k4")
    hold = _reinvoke_packhold()
    assert "k4 reject stale_reflect" in hold


def test_p9_shale():
    """Out-of-window revocation must reject as revoked, not stale_reflect or accept."""
    data = _run_pack()
    _assert_row(data, "p9")
    hold = _reinvoke_packhold()
    assert "p9 reject revoked" in hold


def test_r6_chert():
    """Schema, accept set, reload hold, and surfcheck bait must agree under sealed emit."""
    data = _run_pack()
    assert data["schema_version"] == "pack-admit-1"
    assert data["bind_epoch"] == _runtime_epoch()
    for cid, (decision, reason) in EXPECTED.items():
        row = _rows(data)[cid]
        assert row["decision"] == decision
        assert row["reason_code"] == reason
    accepts = [cid for cid, (d, _) in EXPECTED.items() if d == "accept"]
    assert set(accepts) == {"r6", "m1"}
    _assert_green_surf("r6")
    _assert_green_surf("q3")

    before_epoch = _runtime_epoch()
    before = json.dumps(data, sort_keys=True)
    subprocess.run(
        [PACK_RELOAD],
        check=True,
        cwd="/app",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    after = _load()
    assert after["bind_epoch"] == before_epoch
    assert _runtime_epoch() == before_epoch
    assert json.dumps(after, sort_keys=True) == before
    _assert_prohibited_untouched()
    hold = _reinvoke_packhold()
    assert "r6 accept ok_bound" in hold
    assert "m1 accept ok_bound" in hold
