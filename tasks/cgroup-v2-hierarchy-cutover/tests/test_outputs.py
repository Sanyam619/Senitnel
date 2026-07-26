"""Verifier tests for cgroup v2 hierarchy cutover outcomes."""

import json
import subprocess
from pathlib import Path

REPORT = Path("/output/cutover-report.json")
ANCHOR = Path("/data/fixtures/cgroup-seed")
LEGACY_ROOT = Path("/data/lab/cgroup/v1")
UNIFIED_ROOT = Path("/data/lab/cgroup/unified")
SLICE = "app.slice"

NAMES = ["app-batch.scope", "app-worker.scope", "app-api.scope"]


def _file_sha256(path: Path) -> str:
    result = subprocess.run(
        ["sha256sum", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()[0]


def _load_report() -> dict:
    assert REPORT.exists(), f"missing {REPORT}"
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _scope_map(payload: dict) -> dict[str, dict]:
    scopes = payload.get("scopes")
    assert isinstance(scopes, list)
    return {row["name"]: row for row in scopes if isinstance(row, dict) and "name" in row}


def _node_dir(name: str) -> Path:
    return UNIFIED_ROOT / SLICE / name


def test_x3_shape_bundle():
    """Report covers every scope on the unified tree."""
    payload = _load_report()
    by_name = _scope_map(payload)
    for name in NAMES:
        assert name in by_name, by_name.keys()
        row = by_name[name]
        assert row.get("tree") == "unified", row
        ctrl = str(row.get("controllers", ""))
        assert "io" in ctrl.split()
        assert "memory" in ctrl.split()


def test_f7_brake_hits():
    """IO throttle counters are present in the report."""
    by_name = _scope_map(_load_report())
    for name in NAMES:
        hits = int(by_name[name].get("io_throttle_events", 0))
        assert hits > 0, name


def test_j2_peak_log():
    """Memory peak counters are present in the report."""
    by_name = _scope_map(_load_report())
    for name in NAMES:
        peaks = int(by_name[name].get("memory_high_events", 0))
        assert peaks > 0, name


def test_n5_unit_ledger():
    """Cutover report JSON matches the documented schema."""
    payload = _load_report()
    assert payload.get("version") == 1
    scopes = payload.get("scopes")
    assert isinstance(scopes, list) and len(scopes) >= len(NAMES)
    reported = {row.get("name") for row in scopes if isinstance(row, dict)}
    assert set(NAMES).issubset(reported), reported
    for row in scopes:
        assert isinstance(row.get("name"), str) and row["name"]
        assert row.get("tree") in {"unified", "legacy"}
        assert isinstance(row.get("controllers"), str)
        assert isinstance(row.get("io_throttle_events"), int)
        assert isinstance(row.get("memory_high_events"), int)


def test_p1_shadow_gone():
    """Migrated names no longer have legacy per-controller shadows."""
    for name in NAMES:
        for ctrl in ("cpu", "io", "memory"):
            shadow = LEGACY_ROOT / ctrl / name
            assert not shadow.exists(), shadow


def test_r4_anchor_intact():
    """Anchor seed tree still reflects the pre-cutover snapshot."""
    manifest = ANCHOR / "checksums.sha256"
    assert manifest.is_file(), manifest
    for line in manifest.read_text(encoding="utf-8").splitlines():
        want_hash, rel = line.split(None, 1)
        rel = rel.strip().removeprefix("./")
        path = ANCHOR / rel
        assert path.is_file(), rel
        assert _file_sha256(path) == want_hash, rel


def test_h8_tally_matches_acct():
    """Ledger counters match on-disk accounting files."""
    by_name = _scope_map(_load_report())
    for name in NAMES:
        node = _node_dir(name)
        io_path = node / ".acct/io_brake_hits"
        mem_path = node / ".acct/mem_peak_hits"
        assert io_path.is_file(), io_path
        assert mem_path.is_file(), mem_path
        io_acct = int(io_path.read_text(encoding="utf-8").strip())
        mem_acct = int(mem_path.read_text(encoding="utf-8").strip())
        assert by_name[name]["io_throttle_events"] == io_acct
        assert by_name[name]["memory_high_events"] == mem_acct
        assert io_acct >= 3
        assert mem_acct >= 2


def test_k2_slice_delegation():
    """Slice parent carries io and memory delegation after cutover."""
    sub_path = UNIFIED_ROOT / SLICE / "cgroup.subtree_control"
    assert sub_path.is_file(), sub_path
    tokens = sub_path.read_text(encoding="utf-8").split()
    assert "io" in tokens
    assert "memory" in tokens
